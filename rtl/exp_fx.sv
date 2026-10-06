module exp_fx (
    input logic clk,
    input logic rst_n, //active low reset
    input logic in_valid,
    input logic signed [18:0] x, //signed Q2.16
    output logic out_valid,
    output logic out_of_range, //high if |x| >= 2
    output logic [17:0] y); //e^x, unsigned Q3.15

    //table lookup
    logic [9:0] index; // table index
    logic [17:0] t; //T[idx] from table
    logic [25:0] prod; // t * x_lo

    // verilator lint_off UNUSEDSIGNAL
    logic [25:0] rounded; //low 16 bits intentionally dropped (>> 16)
    //verilator lint_on UNUSEDSIGNAL
    logic [9:0] corr; //round(t * x_lo / 2^16), always < 2^10
    logic [17:0] y_next;

    //pipeline register 1
    logic [17:0] t_q;
    logic [7:0] x_lo_q;
    logic valid_q, oor_q;

    //pipeline register 2
    logic [17:0] t_q2;
    logic [7:0] x_lo_q2;
    logic valid_q2, oor_q2;

    assign index = x[17:8];
    exp_lut lut (.idx(index), .val(t)); //instantitate table


    //register 1
    always_ff @(posedge clk) begin
        if (~rst_n) begin
            valid_q <= 1'b0;
            oor_q <= 1'b0;
            t_q <= 18'd0;
            x_lo_q <= 8'd0;
        end
        else begin
            valid_q <= in_valid;
            oor_q <= (x[18] != x[17]);
            t_q <= t;
            x_lo_q <= x[7:0];
        end
    end

    //register 2
    always_ff @(posedge clk) begin
        if (!rst_n) begin
            valid_q2 <= 1'b0;
            oor_q2 <= 1'b0;
            t_q2 <= 18'd0;
            x_lo_q2 <= 8'd0;
        end
        else begin
            valid_q2 <= valid_q;
            oor_q2 <= oor_q;
            t_q2 <= t_q;
            x_lo_q2 <= x_lo_q;
        end
    end

    always_comb begin
        prod = t_q2 * x_lo_q2;
        rounded = prod + 26'd32768;
        corr = rounded[25:16];
        y_next = t_q2 + {8'd0, corr};
    end

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            out_valid <= 1'b0;
            out_of_range <= 1'b0;
            y <= 18'd0;
        end
        else begin
            out_valid <= valid_q2;
            out_of_range <= oor_q2;
            y <= y_next;
        end
    end
endmodule: exp_fx
