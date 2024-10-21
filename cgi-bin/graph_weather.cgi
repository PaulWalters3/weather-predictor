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

#-----------------------------------------------------------------------------
#
# Program:      graph_weather.cgi
#
# Purpose:      This program is a web CGI script for graphing weather 
#		conditions over the date range given on the web form.
#		This script writes as output HTML for display in a web
#		browser.  This HTML includes JavaScript.  This CGI uses
#		the CGI module for parsing of form variables and uses
#		the GIFgraph module for creating the graphs.
#
#-----------------------------------------------------------------------------

push (@INC, 'pwd');

use CGI;
use DBI;
use Time::Local;
use Chart::Lines;

use Config::Simple;

my $cfg = new Config::Simple(syntax=>'SIMPLE') || die Config::Simple->error();
$cfg->read("$ENV{HOME}/.weather-station.cfg") || $cfg->read("/home/weather/.weather-station.cfg") || die Config::Simple->error();

my $predictStation = $cfg->param('predictStation');

my $dbHost = $cfg->param('dbHost');
my $dbPassword = $cfg->param('dbPassword');
my $dbUser = $cfg->param('dbUser');

my $dbh = DBI->connect( "dbi:mysql:database=weather;host=$dbHost", $dbUser, $dbPassword, { PrintError => 0 });
if ( $DBI::err ) {
    die "$DBI::errstr\n";
}

$query  = new CGI;

# This section begins the output to the web page.  It includes HTML
# and JavaScript.  The JavaScript is code that will be executed by 
# the web browser itself.

print $query->header;
print "<HTML>\n";
print "<HEAD>\n";
print "<TITLE>Hourly Weather Observations and Forecast for $date1 - $date2</TITLE>\n";
print "<SCRIPT>\n";
print "<!-- Hide the JavaScript.\n";
print <<EOT;

var daysInMonth = new Array (31,29,31,30,31,30,31,31,30,31,30,31);

function days_in_month ( month, year )
{
    if ( month != 2 ) {
       return ( daysInMonth[month-1] );
    }
    else {
       return (  ((year % 4 == 0) && ( (!(year % 100 == 0)) || (year % 400 == 0) )) ? 29 : 28 );
    }
}

function dec_date ( which_date, form )
{
    if ( which_date == 1 ) {
        mon = form.mon1.value;
        day = form.day1.value;
        year = form.year1.value;
        hour = form.hour1.value;
        min = form.min1.value;
    }
    else {
        mon = form.mon2.value;
        day = form.day2.value;
        year = form.year2.value;
        hour = form.hour2.value;
        min = form.min2.value;
    }

    day = parseInt(day) - 1;

    if ( parseInt(day) < 1 ) {
        mon = parseInt(mon) - 1;

        if ( parseInt(mon) < 1 ) {
            mon = 12;
            year = parseInt(year) - 1;
        }
        day = days_in_month (parseInt(mon),parseInt(year));
    }

    if ( parseInt(hour) < 10 ) {
        hour = "0" + parseInt(hour);
    }
    if ( parseInt(min) < 10 ) {
        min = "0" + parseInt(min);
    }
    if ( parseInt(mon) < 10 ) {
        mon = "0" + parseInt(mon);
    }
    if ( which_date == 1 ) {
        //form.date1.value = mon+"/"+day+"/"+year+" "+hour+":"+min;
	form.date1.value = year+"-"+mon+"-"+day+" "+hour+":"+min+":00";
        form.mon1.value = parseInt(mon);
        form.day1.value = parseInt(day);
        form.year1.value = parseInt(year);
        form.hour1.value = parseInt(hour);
        form.min1.value = parseInt(min);

        //document.report.date1.value = mon+"/"+day+"/"+year+" "+hour+":"+min;
	document.report.date1.value = year+"-"+mon+"-"+day+" "+hour+":"+min+":00";

        document.report.mon1.value = parseInt(mon);
        document.report.day1.value = parseInt(day);
        document.report.year1.value = parseInt(year);
        document.report.hour1.value = parseInt(hour);
        document.report.min1.value = parseInt(min);
    }
    else {
        //form.date2.value = mon+"/"+day+"/"+year+" "+hour+":"+min;
	form.date2.value = year+"-"+mon+"-"+day+" "+hour+":"+min+":00";
        form.mon2.value = parseInt(mon);
        form.day2.value = parseInt(day);
        form.year2.value = parseInt(year);
        form.hour2.value = parseInt(hour);
        form.min2.value = parseInt(min);

        //document.report.date2.value = mon+"/"+day+"/"+year+" "+hour+":"+min;
	document.report.date2.value = year+"-"+mon+"-"+day+" "+hour+":"+min+":00";
        document.report.mon2.value = parseInt(mon);
        document.report.day2.value = parseInt(day);
        document.report.year2.value = parseInt(year);
        document.report.hour2.value = parseInt(hour);
        document.report.min2.value = parseInt(min);
    }
    return ( true );
}

function inc_date ( which_date, form )
{
    if ( which_date == 1 ) {
        mon = form.mon1.value;
        day = form.day1.value;
        year = form.year1.value;
        hour = form.hour1.value;
        min = form.min1.value;
    }
    else {
        mon = form.mon2.value;
        day = form.day2.value;
        year = form.year2.value;
        hour = form.hour2.value;
        min = form.min2.value;
    }

    day = parseInt(day) + 1;

    if ( parseInt(day) > days_in_month(parseInt(mon),parseInt(year)) ) {
        day = 1;
        mon = parseInt(mon) + 1;
        if ( parseInt(mon) > 12 ) {
            mon = 1;
            year = parseInt(year) + 1;
        }
    }
    if ( parseInt(hour) < 10 ) {
        hour = "0" + parseInt(hour);
    }
    if ( parseInt(min) < 10 ) {
        min = "0" + parseInt(min);
    }
    if ( parseInt(mon) < 10 ) {
        mon = "0" + parseInt(mon);
    }
    if ( which_date == 1 ) {
        //form.date1.value=mon+"/"+day+"/"+year+" "+hour+":"+min;
	form.date1.value = year+"-"+mon+"-"+day+" "+hour+":"+min+":00";
        form.mon1.value = parseInt(mon);
        form.day1.value = parseInt(day);
        form.year1.value = parseInt(year);
        form.hour1.value = parseInt(hour);
        form.min1.value = parseInt(min);

        //document.report.date1.value = mon+"/"+day+"/"+year+" "+hour+":"+min;
	document.report.date1.value = year+"-"+mon+"-"+day+" "+hour+":"+min+":00";
        document.report.mon1.value = parseInt(mon);
        document.report.day1.value = parseInt(day);
        document.report.year1.value = parseInt(year);
        document.report.hour1.value = parseInt(hour);
        document.report.min1.value = parseInt(min);
    }
    else {
        //form.date2.value = mon+"/"+day+"/"+year+" "+hour+":"+min;
	form.date2.value = year+"-"+mon+"-"+day+" "+hour+":"+min+":00";
        form.mon2.value = parseInt(mon);
        form.day2.value = parseInt(day);
        form.year2.value = parseInt(year);
        form.hour2.value = parseInt(hour);
        form.min2.value = parseInt(min);

        //document.report.date2.value = mon+"/"+day+"/"+year+" "+hour+":"+min;
	document.report.date2.value = year+"-"+mon+"-"+day+" "+hour+":"+min+":00";
        document.report.mon2.value = parseInt(mon);
        document.report.day2.value = parseInt(day);
        document.report.year2.value = parseInt(year);
        document.report.hour2.value = parseInt(hour);
        document.report.min2.value = parseInt(min);
    }
    return ( true );
}

function set_time_values ( which_date, form )
{
    var i, j, month, day, year, hour, min;

    month = -1;

    if ( which_date == 1 ) {
        date = form.date1.value;
    }
    else {
        date = form.date2.value;
    }

    for ( i=0, j=0; i < date.length; i++ ) {
        if ((date.substring(i,i+1) == "/") || (date.substring(i,i+1) == "-")) {
            if ( j == 0 ) {
                month = date.substring ( j, i );
                if ( month.charAt(0) == "0" ) {
                    month = month.charAt(1);
                }
            }
            else {
                day = date.substring ( j, i );
                if ( day.charAt(0) == "0" ) {
                    day = day.charAt(1);
                }
            }
            j = i + 1;
        }
        else if ( date.substring(i,i+1) == " " ) {
            year = date.substring ( j, i );
            j = i + 1;
        }
        else if ( date.substring(i,i+1) == ":" ) {
            hour = date.substring ( j, i );
            j = i + 1;
        }
    }

    min = date.substring (j,i);

    if ( parseInt(year) < 100 ) {
        now = new Date();
        var current_year = now.getYear();

        // Netscape and IE return different values.  This check works with
        // either forcing the year to include the century.  It works for any
        // year after 1000.

        if ( current_year < 1000 ) current_year += 1900;

        // Now force the 2-digit year that was entered to a 4-digit year.
        // If it is still the 20th century and they enter a 2-digit
        // year that is less than 50, assume it is for a date in the
        // 21st century.

        if ( (current_year < 2000) && (parseInt(year) < 50) )
            year = parseInt(year) + 2000;
        else
            year = parseInt(year) + 1900;
    }

    if ( parseInt(hour) < 10 ) {
        hour = "0" + parseInt(hour);
    }
    if ( parseInt(min) < 10 ) {
        min = "0" + parseInt(min);
    }
    if ( parseInt(mon) < 10 ) {
        mon = "0" + parseInt(mon);
    }
    if ( which_date == 1 ) {
        form.mon1.value = parseInt(month);
        form.day1.value = parseInt(day);
        form.year1.value = parseInt(year);
        form.hour1.value = parseInt(hour);
        form.min1.value = parseInt(min);
        //form.date1.value = month+"/"+day+"/"+year+" "+hour+":"+min;
	form.date1.value = year+"-"+mon+"-"+day+" "+hour+":"+min+":00";

        document.report.mon1.value = parseInt(month);
        document.report.day1.value = parseInt(day);
        document.report.year1.value = parseInt(year);
        document.report.hour1.value = parseInt(hour);
        document.report.min1.value = parseInt(min);
        //document.report.date1.value = month+"/"+day+"/"+year+" "+hour+":"+min;
	document.report.date1.value = year+"-"+mon+"-"+day+" "+hour+":"+min+":00";
        return ( form.date1.blur() );
    }
    else {
        form.mon2.value = parseInt(month);
        form.day2.value = parseInt(day);
        form.year2.value = parseInt(year);
        form.hour2.value = parseInt(hour);
        form.min2.value = parseInt(min);
        //form.date2.value = month+"/"+day+"/"+year+" "+hour+":"+min;
	form.date2.value = year+"-"+mon+"-"+day+" "+hour+":"+min+":00";

        document.report.mon2.value = parseInt(month);
        document.report.day2.value = parseInt(day);
        document.report.year2.value = parseInt(year);
        document.report.hour2.value = parseInt(hour);
        document.report.min2.value = parseInt(min);
        //document.report.date2.value = month+"/"+day+"/"+year+" "+hour+":"+min;
	document.report.date2.value = year+"-"+mon+"-"+day+" "+hour+":"+min+":00";
        return ( form.date2.blur() );
    }

    return ( true );
}

EOT
print "//-->\n";
print "</SCRIPT>\n";
print "</HEAD>\n";
print "<BODY BGCOLOR=white>\n";

#
# This section determines the date range requested to get the data for.
#
$date1 = $query->param('date1');
$date2 = $query->param('date2');

if ( $date1 eq "" ) {
    ($mon1,$day1,$year1) = (localtime(time()))[4,3,5];
    ($mon2,$day2,$year2) = (localtime(time()))[4,3,5];
    $mon1++;  $year1+=1900; $hour1=0; $min1=0;
    $mon2++;  $year2+=1900; $hour2=23; $min2=59;
    $date1=sprintf ("%04d-%02d-%02d %02d:%02d:00",$year1,$mon1,$day1,$hour1,$min1);
    $date2=sprintf ("%04d-%02d-%02d %02d:%02d:00",$year2,$mon2,$day2,$hour2,$min2);
}
else {
    ($year1,$mon1,$day1,$hour1,$min1) = split (/[\-\s\:]/, $date1);
    if ( $date2 eq "" ) {
        ($year2,$mon2,$day2,$hour2,$min2) = split (/\-\s\:/, $date1);
        $date2=sprintf("%04d-%02d-%02d %02d:%02d:00",$year2,$mon2,$day2,
                                                       $hour2,$min2);
    }
    else {
        ($year2,$mon2,$day2,$hour2,$min2) = split (/[\-\s\:]/, $date2);
    }
}

#
# This section prepares the proper database query to get the data needed
# to generate the graphs for the requested date range.
#
$query = "SELECT date_format(p.time,'%m/%d %H:%i') as obs_time,
                 a.temperature as a_temperature, p.temperature as p_temperature, a.humidity as a_humidity, p.humidity as p_humidity,
                 a.wind_direction as a_wind_direction, p.wind_direction as p_wind_direction, a.wind_speed as a_wind_speed,
                 p.wind_speed as p_wind_speed, a.pressure as a_pressure, p.pressure as p_pressure,
                 ifnull(a.weather,'&nbsp;') as a_weather, ifnull(p.weather,'&nbsp;') as p_weather
            FROM predicted p
                 left outer join observations a on
                         a.site = '$predictStation' AND 
			 (a.time BETWEEN '$date1' AND '$date2') and
			abs(unix_timestamp(a.time)-unix_timestamp(p.time)) < 1800
           WHERE p.time BETWEEN '$date1' AND '$date2'
           ORDER BY p.time ";
print "<!--\n$query\n-->\n";
$sth = $dbh->prepare ( $query );
die "$DBI::errstr\n" if ( $DBI::err > 0 );
$sth->execute;

print "<CENTER>";

print "<FONT SIZE=+1>Hourly Weather Observations and Forecast for $date1 - $date2</FONT><P>\n";

print <<EOT;
<FONT SIZE=-1>This site is for entertainment purposes only.  It is not a source of reliable weather forecasts.<P>
</FONT>
Weather predictions on this site are made 12-hours ahead of the forecast period for the prediction station.<BR>
All forecasts are computer-generated.  A simple neural network is used for each of the forecasted conditions.<P>
EOT

$idx = 0;
@temp_data = ();
@humidity_data = ();
@pressure_data = ();
@wind_speed_data = ();

# Fetch the data from the query and store the temperature, humidity, wind
# speed, and pressure in data arrays that will be used by the GIFgraph 
# module to create the graphs.
while ( $ref = $sth->fetchrow_hashref() ) {


        $obs_time = $ref->{obs_time};
        $a_temperature = $ref->{a_temperature};
        $p_temperature = $ref->{p_temperature};
        $a_humidity = $ref->{a_humidity};
        $p_humidity = $ref->{p_humidity};
        $a_wind_direction = $ref->{a_wind_direction};
        $p_wind_direction = $ref->{p_wind_direction};
        $a_wind_speed = $ref->{a_wind_speed};
        $p_wind_speed = $ref->{p_wind_speed};
        $a_pressure = $ref->{a_pressure};
        $p_pressure = $ref->{p_pressure};
        $a_weather = $ref->{a_weather};
        $p_weather = $ref->{p_weather};

    $temp_data[0][$idx] = $obs_time;
    $temp_data[1][$idx] = sprintf "%.0f", $a_temperature;
    $temp_data[1][$idx] = undef if ( $a_temperature eq "" );
    $temp_data[2][$idx] = sprintf "%.0f", $p_temperature;
    $temp_data[2][$idx] = undef if ( $p_temperature eq "" );

    $humidity_data[0][$idx] = $obs_time;
    $humidity_data[1][$idx] = sprintf "%.0f", $a_humidity;
    $humidity_data[1][$idx] = undef if ( $a_humidity eq "" );
    $humidity_data[2][$idx] = sprintf "%.0f", $p_humidity;
    $humidity_data[2][$idx] = undef if ( $p_humidity eq "" );

    $pressure_data[0][$idx] = $obs_time;
    $pressure_data[1][$idx] = sprintf "%.02f", $a_pressure;
    $pressure_data[1][$idx] = undef if ( $a_pressure eq "" );
    $pressure_data[2][$idx] = sprintf "%.02f", $p_pressure;
    $pressure_data[2][$idx] = undef if ( $p_pressure eq "" );

    $wind_speed_data[0][$idx] = $obs_time;
    $wind_speed_data[1][$idx] = sprintf "%.02f", $a_wind_speed;
    $wind_speed_data[1][$idx] = undef if ( $a_wind_speed eq "" );
    $wind_speed_data[2][$idx] = sprintf "%.02f", $p_wind_speed;
    $wind_speed_data[2][$idx] = undef if ( $p_wind_speed eq "" );

    $idx++;
}

$sth->finish;

# Now use the GIFgraph module to create each of the graphs.
#
$x_label_skip = (($idx-1) / 24) + 2; 

$fn = "/tmp/temperature.$$.png";
@legend=('Actual','Predicted');
$temp_graph = new Chart::Lines(800,300);
$temp_graph->set ( x_label => 'Time',
                   y_label => 'Degrees (F)',
                   title   => 'Temperature: Actual vs. Predicted',
                   x_ticks => 1,
                   long_ticks => 1,
                   brush_size => 2,
                   x_ticks => 'vertical',
		   integer_ticks_only => 1,
                   skip_x_ticks => $x_label_skip);
$temp_graph->set ( 'legend_labels' => \@legend );
$temp_graph->png ( $fn, \@temp_data );
print "<IMG SRC=\"/weather/cgi-bin/show_image.cgi?image=$fn\"><P>";

$fn = "/tmp/humidity.$$.png";
$humidity_graph = new Chart::Lines(800,300);
$humidity_graph->set ( x_label => 'Time',
                   y_label => 'Relative Humidity (%)',
                   title   => 'Humidity: Actual vs. Predicted',
                   x_ticks => 1,
                   long_ticks => 1,
                   brush_size => 2,
                   x_ticks => 'vertical',
		   integer_ticks_only => 1,
                   skip_x_ticks => $x_label_skip);
	$humidity_graph->set ( 'legend_labels' => \@legend );
$humidity_graph->png ( $fn, \@humidity_data );
print "<IMG SRC=\"/weather/cgi-bin/show_image.cgi?image=$fn\"><P>";

$fn = "/tmp/pressure.$$.png";
$pressure_graph = new Chart::Lines(800,300);
$pressure_graph->set ( x_label => 'Time',
                   y_label => 'Pressure (inches)',
                   title   => 'Pressure: Actual vs. Predicted',
                   x_ticks => 1,
                   long_ticks => 1,
                   brush_size => 2,
                   x_ticks => 'vertical',
		   integer_ticks_only => 1,
                   skip_x_ticks => $x_label_skip);
$pressure_graph->set ( 'legend_labels' => \@legend );
$pressure_graph->png ( $fn, \@pressure_data );
print "<IMG SRC=\"/weather/cgi-bin/show_image.cgi?image=$fn\"><P>";

$fn = "/tmp/wind_speed.$$.png";
$wind_speed_graph = new Chart::Lines(800,300);
$wind_speed_graph->set ( x_label => 'Time',
                   y_label => 'Speed (MPH)',
                   title   => 'Wind Speed: Actual vs. Predicted',
                   x_ticks => 1,
                   long_ticks => 1,
                   brush_size => 2,
                   x_ticks => 'vertical',
		   integer_ticks_only => 1,
                   skip_x_ticks => $x_label_skip);
$wind_speed_graph->set ( 'legend_labels' => \@legend );
$wind_speed_graph->png ( $fn, \@wind_speed_data );
print "<IMG SRC=\"/weather/cgi-bin/show_image.cgi?image=$fn\"><P>";

#
# Now finish up the page by creating a new form so the user can again
# query the database.
#
print "<FORM NAME=report ACTION=\"/weather/cgi-bin/weather.cgi\" METHOD=post>\n";

print "<INPUT TYPE=hidden NAME=mon1 VALUE=\"$mon1\">\n";
print "<INPUT TYPE=hidden NAME=day1 VALUE=\"$day1\">\n";
print "<INPUT TYPE=hidden NAME=year1 VALUE=\"$year1\">\n";
print "<INPUT TYPE=hidden NAME=hour1 VALUE=\"$hour1\">\n";
print "<INPUT TYPE=hidden NAME=min1 VALUE=\"$min1\">\n";

print "<INPUT TYPE=hidden NAME=mon2 VALUE=\"$mon2\">\n";
print "<INPUT TYPE=hidden NAME=day2 VALUE=\"$day2\">\n";
print "<INPUT TYPE=hidden NAME=year2 VALUE=\"$year2\">\n";
print "<INPUT TYPE=hidden NAME=hour2 VALUE=\"$hour2\">\n";
print "<INPUT TYPE=hidden NAME=min2 VALUE=\"$min2\">\n";

print "<INPUT TYPE=hidden NAME=date1 VALUE=\"$date1\">\n";
print "<INPUT TYPE=hidden NAME=date2 VALUE=\"$date2\">\n";
print "</FORM>\n";

print "<FORM ACTION=\"/weather/cgi-bin/graph_weather.cgi\" METHOD=post>\n";

print "<INPUT TYPE=hidden NAME=mon1 VALUE=\"$mon1\">\n";
print "<INPUT TYPE=hidden NAME=day1 VALUE=\"$day1\">\n";
print "<INPUT TYPE=hidden NAME=year1 VALUE=\"$year1\">\n";
print "<INPUT TYPE=hidden NAME=hour1 VALUE=\"$hour1\">\n";
print "<INPUT TYPE=hidden NAME=min1 VALUE=\"$min1\">\n";

print "<INPUT TYPE=hidden NAME=mon2 VALUE=\"$mon2\">\n";
print "<INPUT TYPE=hidden NAME=day2 VALUE=\"$day2\">\n";
print "<INPUT TYPE=hidden NAME=year2 VALUE=\"$year2\">\n";
print "<INPUT TYPE=hidden NAME=hour2 VALUE=\"$hour2\">\n";
print "<INPUT TYPE=hidden NAME=min2 VALUE=\"$min2\">\n";

print "&nbsp;<BR>Enter date range for observations and forecasts:<BR>";
print "<INPUT TYPE=text VALUE=\"$date1\" NAME=date1 SIZE=16";
print " onChange=\"return(set_time_values(1, this.form));\"> ";

print "<INPUT TYPE=\"button\" VALUE=\"<\" ";
print "onClick=\"return(dec_date(1, this.form));\">\n";

print "<INPUT TYPE=\"button\" VALUE=\">\" ";
print "onClick=\"return(inc_date(1, this.form));\">\n";

print " - ";
print "<INPUT TYPE=text VALUE=\"$date2\" NAME=date2 SIZE=16";
print " onChange=\"return(set_time_values(2, this.form));\">";

print "<INPUT TYPE=\"button\" VALUE=\"<\" ";
print "onClick=\"return(dec_date(2, this.form));\">\n";

print "<INPUT TYPE=\"button\" VALUE=\">\" ";
print "onClick=\"return(inc_date(2, this.form));\">\n";

print "<BR>&nbsp;<BR>";

print "<INPUT TYPE=submit VALUE=\"Weather Graphs\">";
print "&nbsp; <INPUT TYPE=button VALUE=\"Weather Report\" onClick=\"return(report.submit());\">";
print "</FORM>\n";

print "</CENTER>\n";

$dbh->disconnect;
print $query->end_html;
exit 0;

sub get_wind_direction 
{
    ($degrees) = @_;

    if ( $degrees == 0 ) { return 'North'; }
    if ( $degrees == 22.5 ) { return 'NNE'; }
    if ( $degrees == 45 ) { return 'NE'; }
    if ( $degrees == 67.5 ) { return 'ENE'; }
    if ( $degrees == 90 ) { return 'East'; }
    if ( $degrees == 112.5 ) { return 'ESE'; }
    if ( $degrees == 135 ) { return 'SE'; }
    if ( $degrees == 157.5 ) { return 'SSE'; }
    if ( $degrees == 180 ) { return 'South'; }
    if ( $degrees == 202.5 ) { return 'SSW'; }
    if ( $degrees == 225 ) { return 'SW'; }
    if ( $degrees == 247.5 ) { return 'WSW'; }
    if ( $degrees == 270 ) { return 'West'; }
    if ( $degrees == 292.5 ) { return 'WNW'; }
    if ( $degrees == 315 ) { return 'NW'; }
    if ( $degrees == 337.5 ) { return 'NNW'; }
    return "";
}

