#!/usr/bin/perl

# Copyright 1997-2024 Paul Walters
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

use strict;

use DBI;

sub openDatabase
{
	my $dbHost = shift;
	my $dbUser = shift;
	my $dbPassword = shift;

	my $dbh = DBI->connect( "dbi:mysql:database=weather;host=$dbHost", $dbUser, $dbPassword, { PrintError => 0 });
	die "$DBI::errstr\n" if ( $DBI::err > 0 );
	return $dbh;
}

sub getSites
{
	my $dbh = shift;
	my $predictStation = shift;
	my $ignoreSites = shift;

	my $query = "SELECT site FROM sites WHERE site != '$predictStation'";

	foreach my $ignore (@$ignoreSites) {
		$query .= " and site != '$ignore'";
	}

	# print "$query\n";

	# Get a list of sites that data is being collected from excluding
	# the prediction site and any sites to ignore.

	my $sth = $dbh->prepare ( $query );
	$sth->execute;
	my @sids = ();
	while ( my $row = $sth->fetchrow_hashref() ) {
    		push (@sids, $$row{site});
    		print "Found $$row{site}\n";
	}
	$sth->finish;

	die "No sites.\n" if ( @sids < 1 );

	return sort @sids;
}

sub getLastObservationTime
{
	my $dbh = shift;
	my $predictStation = shift;

	my $query = "SELECT max(time) as last_obs FROM observations WHERE site = '$predictStation'";
	my $sth = $dbh->prepare ( $query );
	$sth->execute;
	my $ref = $sth->fetchrow_hashref();
	$sth->finish;

    	return $ref->{last_obs};
}

sub computePredictionTime
{
	my ($forecastPeriod, $last_obs) = @_;

	my ($year,$mon,$day,$hour,$min) = ($last_obs =~ /(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2})/);
	$mon=int($mon)-1; $year-=1900;

	my $prediction_time = timelocal(0,0,$hour,$day,$mon,$year);
	$prediction_time += ($forecastPeriod * 3600);

	($mon,$day,$year,$hour) = (localtime($prediction_time))[4,3,5,2];
	$mon++; $year+=1900;

	my $forecast_time = sprintf ("%04d-%02d-%02d %02d:00", $year,$mon,$day,$hour);

	return $forecast_time;
}

sub checkForPrediction
{
	my ( $dbh, $forecast_time, $type ) = @_;

	my $query = "
		SELECT count(*) as already_done FROM predicted
		WHERE time = '$forecast_time'
		and $type IS NOT NULL
	";
	my $sth = $dbh->prepare ( $query );
	$sth->execute;
	my $ref = $sth->fetchrow_hashref();
	$sth->finish;

	return $ref->{already_done};
}

sub decodePWX
{
	my ( $type, $result ) = @_;

	## The threshold that a given condition is present.  Based simply on me 
	## looking at results compared against actual conditions.  

	my %THRESHOLD = (
		"CLOUDS"  => 0.3,
		"ICE"	  => 0.23,
		"RAIN"	  => 0.23,

		##"SNOW" 	  => 0.12,	# 0.1021 is clearly no snow.  I do see instances
						# even in the 0.3's where there is snow and not
						# snow though.  But I think I'd rather call it than not.
		"SNOW" => 0.14,	## Changed from 0.12 to 0.14 on 2021-01-08
		"THUNDER" => 0.3,
	);

	chomp($result);
	$result =~ s/^\s+//g;
	$result =~ s/\s+$//g;

	my ( $condition, $intensity ) = split(/\s+/,$result);
	$condition =~ s/^\s+//g;
	$condition =~ s/\s+$//g;
	$intensity =~ s/^\s+//g;
	$intensity =~ s/\s+$//g;

	my $weather = "";

	if ( $type eq "CLOUDS" && $condition > $THRESHOLD{$type} ) {
		if ( $intensity > 0.8  ) {
			$weather .= "Overcast ";
		}
		elsif ( $intensity > 0.5 ) {
			$weather .= "Mostly Cloudy ";
		}
		else { ## if ( $intensity > 0.2 ) {
			$weather .= "Partly Cloudy ";
		}
	}

	if ( $type eq "RAIN" && $condition > $THRESHOLD{$type} ) {
		if ( $intensity > 0.7  ) {
			$weather .= "Heavy Rain ";
		}
		elsif ( $intensity > 0.45) {
			$weather .= "Rain ";
		}
		else { ## if ( $intensity > 0.2 ) {
			$weather .= "Light Rain ";
		}
	}

	if ( $type eq "SNOW" && $condition > $THRESHOLD{$type} ) {
		if ( $intensity > 0.7  ) {
			$weather .= "Heavy Snow ";
		}
		elsif ( $intensity > 0.45) {
			$weather .= "Snow ";
		}
		else { ## if ( $intensity > 0.2 ) {
			$weather .= "Light Snow ";
		}
	}

	if ( $type eq "ICE" && $condition > $THRESHOLD{$type} ) {
		if ( $intensity > 0.7  ) {
			$weather .= "Heavy Ice ";
		}
		elsif ( $intensity > 0.45 ) {
			$weather .= "Ice ";
		}
		else { ## if ( $intensity > 0.2 ) {
			$weather .= "Light Ice ";
		}
	}

	if ( $type eq "THUNDER" && $condition > $THRESHOLD{$type} ) {
		if ( $intensity > 0.7  ) {
			$weather .= "Heavy Thunderstorms ";
		}
		elsif ( $intensity > 0.45 ) {
			$weather .= "Thunderstorms ";
		}
		else { ## if ( $intensity > 0.2 ) {
			$weather .= "Isolated Thunderstorms ";
		}
	}

	$weather =~ s/\s*$//;

	return $weather;
}

sub outputPWX
{
	my ( $pwx, $forecastPeriod, $suffix, $newLine, $debug ) = @_;

	my $clouds = 0.1; my $cloudIntensity = 0.1;
	my $rain = 0.1; my $rainIntensity = 0.1;
	my $snow = 0.1; my $snowIntensity = 0.1;
	my $ice = 0.1; my $iceIntensity = 0.1;
	my $thunder = 0.1; my $thunderIntensity = 0.1;

	if ( $pwx =~ /cloud/ || $pwx =~ /overcast/ || $pwx =~ /fog/ || $pwx =~ /fair/ ) {
		if ( $pwx =~ /freezing fog/ ) {
			$ice = 0.9;
			$iceIntensity = 0.3;
		}
		if ( $pwx =~ /scattered/ || $pwx =~ /partly/ || $pwx =~ /fog/ || $pwx =~ /fair/ || $pwx =~/few/) {
			$clouds = 0.9;
			$cloudIntensity = 0.3;
		}
		elsif ( $pwx =~ /overcast/ ) {
			$clouds = 0.9;
			$cloudIntensity = 0.9;
		}
		else {
			$clouds = 0.9;
			$cloudIntensity = 0.6;
		}
	}
	
      	if ( $pwx =~ /thunder/ ) {
		$rain = 0.9;
		$thunder = 0.9;
		if ( $pwx =~ /light/ ) {
      			$thunderIntensity = 0.3;
      			$rainIntensity = 0.3;
		}
		elsif ( $pwx =~ /heavy/ ) {
      			$thunderIntensity = 0.9;
      			$rainIntensity = 0.9;
		}
		else {
      			$thunderIntensity = 0.6;
      			$rainIntensity = 0.6;
		}
	}

	if ( $pwx =~ /rain/ || $pwx =~ /drizzle/ || $pwx =~ /mist/ || $pwx =~ /ice/ || $pwx =~ /sleet/ ) {
		if ( $pwx =~ /ice/ || $pwx =~ /sleet/ || $pwx =~ /freezing/ ) {
			$ice = 0.9;
			if ( $pwx =~ /fog/ || $pwx =~ /drizzle/ || $pwx =~ /light/ ) {
				$iceIntensity = 0.3;
			}
			elsif ( $pwx =~ /heavy/ ) {
				$iceIntensity = 0.9;
			}
			else {
				$iceIntensity = 0.60;
			}
		}
		else {
			$rain = 0.9;
			if ( $pwx =~ /mist/ || $pwx =~ /drizzle/ || $pwx =~ /light/ ) {
				$rainIntensity = 0.3;
			}
			elsif ( $pwx =~ /heavy/ ) {
				$rainIntensity = 0.9;
			}
			else {
				$rainIntensity = 0.6;
			}
		}
	}

	if ( $pwx =~ /snow/ ) {
		$snow = 0.9;
		if ( $pwx =~ /light/ ) {
			$snowIntensity = 0.3;
		}
		elsif ( $pwx =~ /heavy/ ) {
			$snowIntensity = 0.9;
		}
		else {
			$snowIntensity = 0.6;
		}
	}

	if ( fileno(CLOUDS) == undef ) {
		open ( CLOUDS, ">CLOUDS${forecastPeriod}${suffix}" ) || die "Cannot open CLOUDS${forecastPeriod}${suffix} (!$).\n";
		open ( RAIN, ">RAIN${forecastPeriod}${suffix}" ) || die "Cannot open RAIN${forecastPeriod}${suffix} (!$).\n";
		open ( SNOW, ">SNOW${forecastPeriod}${suffix}" ) || die "Cannot open SNOW${forecastPeriod}${suffix} (!$).\n";
		open ( ICE, ">ICE${forecastPeriod}${suffix}" ) || die "Cannot open ICE${forecastPeriod}${suffix} (!$).\n";
		open ( THUNDER, ">THUNDER${forecastPeriod}${suffix}" ) || die "Cannot open THUNDER${forecastPeriod}${suffix} (!$).\n";
	}

      	printf CLOUDS "%f %f ", $clouds, $cloudIntensity;
	print CLOUDS "\n" if ( $newLine );

      	printf RAIN "%f %f ", $rain, $rainIntensity;
	print RAIN "\n" if ( $newLine );

      	printf SNOW "%f %f ", $snow, $snowIntensity;
	print SNOW "\n" if ( $newLine );

      	printf ICE "%f %f ", $ice, $iceIntensity;
	print ICE "\n" if ( $newLine );

      	printf THUNDER "%f %f ", $thunder, $thunderIntensity;
	print THUNDER "\n" if ( $newLine );

	if ( $debug ) {
      		printf "$pwx (%f %f %f %f %f) (%f %f %f %f %f)\n", $clouds, $rain, $snow, $ice, $thunder, $cloudIntensity, $rainIntensity, $snowIntensity, $iceIntensity, $thunderIntensity;
	}
}

sub outputWD
{
	my ( $wind, $forecastPeriod, $suffix, $newLine, $debug ) = @_;

	if ( fileno(WD) == undef ) {
		open ( WD, ">WD${forecastPeriod}${suffix}" ) || die "Cannot open WD${forecastPeriod}${suffix} (!$).\n";
	}

	my $north = my $ne = my $east = my $se = my $south = my $sw = my $west = my $nw = 0.0;

	if ( ($wind < 22.5) || ($wind > 337.5) ) {
		$north = 1.0;
	}
	elsif (($wind >= 22.5) && ($wind <= 67.5)) {
		$ne = 1.0;
	}
	elsif (($wind > 67.5) && ($wind < 112.5)) {
		$east = 1.0;
	}
	elsif (($wind >= 112.5) && ($wind <= 157.5)) {
		$se = 1.0;
	}
	elsif (($wind > 157.5) && ($wind < 202.5)) {
		$south = 1.0;
	}
	elsif (($wind >= 202.5) && ($wind <= 247.5)) {
		$sw = 1.0;
	}
	elsif (($wind > 247.5) && ($wind < 292.5)) {
		$west = 1.0;
	}
	elsif (($wind >= 292.5) && ($wind <= 337.5)) {
		$nw = 1.0;
	}

	printf WD "%f %f %f %f %f %f %f %f ", $north, $ne, $east, $se, $south, $sw, $west, $nw;
	print WD "\n" if ( $newLine );

	if ( $debug ) {
		printf "Wind Direction (%s %f %f %f %f %f %f %f %f)\n", $wind, $north, $ne, $east, $se, $south, $sw, $west, $nw;
	}
}

sub outputWS
{
	my ( $wind, $forecastPeriod, $suffix, $newLine, $debug ) = @_;

	if ( fileno(WS) == undef ) {
		open ( WS, ">WS${forecastPeriod}${suffix}" ) || die "Cannot open WS${forecastPeriod}${suffix} (!$).\n";
	}

      	printf WS "%f ", scale(0,70,$wind);
	print WS "\n" if ( $newLine );

	if ( $debug ) {
      		printf "Wind Speed (%f)\n", $wind;
	}
}

sub outputHumidity
{
	my ( $temperature, $humidity, $forecastPeriod, $suffix, $hour, $debug ) = @_;

	if ( $hour ne "" && fileno(HUMIDITY) != undef ) {
		print HUMIDITY "\n";
	}

	if ( fileno(HUMIDITY) == undef ) {
		open ( HUMIDITY, ">HUMIDITY${forecastPeriod}${suffix}" ) || die "Cannot open HUMIDITY${forecastPeriod}${suffix} (!$).\n";
	}

	#printf HUMIDITY "%f ", scale(0,23,$hour) if ( $hour ne "" );
	printf HUMIDITY "%f ", $hour if ( $hour ne "" );

	$temperature = scale(-20, 110, $temperature) if ($temperature ne "");
	$humidity = scale(0, 100, $humidity);

	printf HUMIDITY "%f ", $temperature if ($temperature ne "");
	printf HUMIDITY "%f ", $humidity;

	if ( $debug ) {
		printf "Temperature (%f) Humidity (%f)\n", $temperature, $humidity;
	}
}

sub outputPressure
{
	my ( $pressure, $forecastPeriod, $suffix, $newLine, $debug ) = @_;

	if ( fileno(PRESSURE) == undef ) {
		open ( PRESSURE, ">PRESSURE${forecastPeriod}${suffix}" ) || die "Cannot open PRESSURE${forecastPeriod}${suffix} (!$).\n";
	}

	$pressure = scale(25, 35, $pressure);

      	printf PRESSURE "%f ", $pressure;
	print PRESSURE "\n" if ( $newLine );
	
	if ( $debug ) {
      		printf "Pressure (%f)\n", $pressure;
	}
}
sub outputTemperature
{
	my ( $temperature, $forecastPeriod, $suffix, $hour, $debug ) = @_;

	if ( $hour ne "" && fileno(TEMP) != undef ) {
		print TEMP "\n";
	}

	if ( fileno(TEMP) == undef ) {
		open ( TEMP, ">TEMPERATURE${forecastPeriod}${suffix}" ) || die "Cannot open TEMPERATURE${forecastPeriod}${suffix} (!$).\n";
	}

	#printf TEMP "%f", scale(0,23,$hour) if ( $hour ne "" );
	printf TEMP "%f", $hour if ( $hour ne "" );

	if ($suffix eq '.csv') {
      		printf TEMP ",%f", $temperature;
	}
	else {
		$temperature = scale(-20, 110, $temperature);

      		printf TEMP " %f", $temperature;
		#printf TEMP " %f\n", ($hour/100) if ( $newLine );

		if ( $debug ) {
			printf "Temperature (%f)\n", $temperature;
		}
	}
}

sub unscale
{
    my ($min, $max, $value) = @_;

    my $scale = 0.8 / ($max - $min);

    my $ret_value = (($value - 0.1) / $scale ) + $min;

    return $ret_value;
}

sub scale
{
    my ($min, $max, $value) = @_;

    my $scale = 0.8 / ($max - $min);

    my $ret_value = $scale * ( $value - $min ) + 0.1;

    return $ret_value;
}

END {
	close( CLOUDS ) if ( defined fileno(CLOUDS) );
	close( RAIN ) if ( defined fileno(RAIN) );
	close( SNOW ) if ( defined fileno(SNOW) );
	close( ICE ) if ( defined fileno(ICE) );
	close( THUNDER ) if ( defined fileno(THUNDER) );
	close( WD ) if ( defined fileno(WD) );
	close( WS ) if ( defined fileno(WS) );
	close( TEMP ) if ( defined fileno(TEMP) );
	close( HUMIDITY ) if ( defined fileno(HUMIDITY) );
	close( PRESSURE ) if ( defined fileno(PRESSURE) );
};

1;
