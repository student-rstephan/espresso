# Copyright (C) 2010,2011 The ESPResSo project
# Copyright (C) 2002,2003,2004,2005,2006,2007,2008,2009,2010 Max-Planck-Institute for Polymer Research, Theory Group, PO Box 3148, 55021 Mainz, Germany
#  
# This file is part of ESPResSo.
#  
# ESPResSo is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#  
# ESPResSo is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#  
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>. 

source "tests_common.tcl"

puts "-------------------------------------------"
puts "- Testcase uwerr.tcl running on [format %02d [setmd n_nodes]] nodes: -"
puts "-------------------------------------------"

set nrep { 1000 1000 1000 1000 1000 1000 1000 1000 }

proc blubb {vec} {
   return [expr -1 * log([lindex $vec 1] / [lindex $vec 0])]
}

set df [open "uwerr_test.data" r]
while {![eof $df]} {
   gets $df row
   lappend data [split $row " "]
}
close $df
set data [lrange $data 0 end-1]

puts "Expected values:"
puts "0.190161129416 0.0149872743495 0.00120248945994 8.70337780606 1.27314416767 0.992579964046"
puts [uwerr $data $nrep blubb plot]

exit 1
