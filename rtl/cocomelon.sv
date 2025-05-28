module cocomelon #(
    parameter DATA_WIDTH = 8,
    parameter ADDR_WIDTH = 3
) (
    input i_wclk, i_wrst_n, i_wr_en,
    input [DATA_WIDTH-1:0] i_wdata,
    output o_wfull,

    input i_rclk, i_rrst_n, i_rd_en,
    output [DATA_WIDTH-1:0] o_rdata,
    output o_rempty
);
    logic [ADDR_WIDTH:0] wbin;
    logic [ADDR_WIDTH:0] rbin;
    logic [DATA_WIDTH-1:0] mem [0:(1<<ADDR_WIDTH)-1];

    logic [ADDR_WIDTH:0] wgray, rgray;
    logic [ADDR_WIDTH:0] rq1_wgray, rq2_wgray;
    logic [ADDR_WIDTH:0] wq1_rgray, wq2_rgray;

    // write pointer
    initial wbin = 0;

    always @(posedge i_wclk or negedge i_wrst_n) begin
        if (!i_wrst_n) begin
            wbin <= 0;
        end
        else if ((i_wr_en)&&(!o_wfull)) begin
            wbin <= wbin + 1;
        end
    end

    always @(posedge i_wclk) begin
        if ((i_wr_en)&&(!o_wfull)) begin
            mem[wbin[ADDR_WIDTH-1:0]] <= i_wdata;
        end
    end

    // reading 
    initial rbin = 0;

    always @(posedge i_rclk or negedge i_rrst_n) begin
        if (!i_rrst_n) begin
            rbin <= 0;
        end
        else if ((i_rd_en)&&(!o_rempty)) begin
            rbin <= rbin + 1;
        end
    end

    // metastability with gray coding

    // flip flops
    always @(posedge i_wclk)  
        wgray <= (wbin >> 1) ^ wbin;
    always @(posedge i_rclk)  
        rgray <= (rbin >> 1) ^ rbin;

    always @(posedge i_rclk or negedge i_rrst_n)
        if (!i_rrst_n)
            {rq2_wgray, rq1_wgray} <= 0;
        else
            {rq2_wgray, rq1_wgray} <= {rq1_wgray, wgray};
    
    always @(posedge i_wclk or negedge i_wrst_n)
        if (!i_wrst_n)
            {wq2_rgray, wq1_rgray} <= 0;
        else
            {wq2_rgray, wq1_rgray} <= {wq1_rgray, rgray};

    assign o_rdata = mem[rbin[ADDR_WIDTH-1:0]];

    assign o_wfull = (wgray[ADDR_WIDTH:ADDR_WIDTH-1] == ~wq2_rgray[ADDR_WIDTH:ADDR_WIDTH-1]) &&
                     (wgray[ADDR_WIDTH-2:0] == wq2_rgray[ADDR_WIDTH-2:0]);

    assign o_rempty = (rgray == rq2_wgray);

endmodule