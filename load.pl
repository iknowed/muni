#!/usr/bin/perl
use warnings;
use strict;
use Text::CSV;
use DBI;
my $pghost="cybre.net";
my $pgport="5432";
my $pgoptions ="";
my $pgtty =""; 
my $dbname ="routing";
my $login="";
my $pwd ="";
my $conn = DBI->connect("dbi:Pg:dbname=$dbname;host=$pghost;port=$pgport;" 
                      , "$login", "$pwd");


my $csv = Text::CSV->new ( { binary => 1 } )  # should set binary attribute.
   or die "Cannot use CSV: ".Text::CSV->error_diag ();
my(@rows);
my $shape_ids;
foreach my $txt ( <../gtfs/*.txt>) { 
	open my $fh, "<:encoding(utf8)", $txt or die "test.csv: $!";
	my($table) = ($txt =~ m/\/([^\/]+)\.txt$/);
	next unless($table eq "stop_times");
	print "$table\n";
	my $schema = $csv->getline($fh);	
	my $qs = join(",",map { "?" } @$schema);
	my $schema = join(",",@{$schema});
	while ( my $row = $csv->getline( $fh ) ) {
		#next if(($table eq "shapes") && $shape_ids->{$row->[0]});
		if($table eq "stop_times") {
			$row->[0] = 1;
		}
		$shape_ids->{$row->[0]} = 1;
		my $sql = "insert into $table ($schema) values($qs)";
		my $sth = $conn->prepare($sql);
		$sth->execute(@$row);
		if($conn->errstr) {
			print $conn->errstr."\n";
		}
        }
}
