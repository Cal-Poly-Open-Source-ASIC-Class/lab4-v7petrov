create_clock [get_ports i_rclk] -name i_rclk -period 7
set_propagated_clock i_rclk
create_clock [get_ports i_wclk] -name i_wclk -period 14
set_propagated_clock i_wclk

set_clock_groups -asynchronous -group [get_clocks {i_rclk i_wclk}]

set read_period     [get_property -object_type clock [get_clocks {i_rclk}] period]
set write_period    [get_property -object_type clock [get_clocks {i_wclk}] period]
set min_period      [expr {min($read_period, $write_period)}]

set_max_delay -from [get_pins wgray*df*/CLK] -to [get_pins rq1_wgray*df*/D] $min_period
set_max_delay -from [get_pins rgray*df*/CLK] -to [get_pins wq1_rgray*df*/D] $min_period