#!/usr/bin/perl
use warnings;
use strict;
use DBI;
my $pghost="cybre.net";
my $pgport="5432";
my $pgoptions ="";
my $pgtty =""; 
my $dbname ="municonsole1";
my $login="";
my $pwd ="";
my $conn = DBI->connect("dbi:Pg:dbname=$dbname;host=$pghost;port=$pgport;" 
                      , "$login", "$pwd");
my $conn1 = DBI->connect("dbi:Pg:dbname=$dbname;host=$pghost;port=$pgport;" 
                      , "$login", "$pwd");

my $sql = "select route_id,line,direction,numtag,tag from lines";
my $sth = $conn->prepare($sql);
$sth->execute();
while(my($row) = $sth->fetchrow_arrayref()) {
	next unless($row);
	my $route_id = $row->[0];
	my $line = $row->[1];
	my $direction = $row->[2];
	$line =~ s/^[0]+//g;	
	$line =~ s/\-/ /g;
	$line =~ s/114/14/g;
	print "$line $row->[4]\n";
	my $sql = "update lines set tag=? where line=?";
	my $sti = $conn1->prepare($sql);
	$sti->execute($line,$row->[4]);
}
