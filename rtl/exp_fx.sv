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
    logic [7:0] x_lo; 
    logic [17:0] t; //T[idx] from table
    logic [25:0] prod; // t * x_lo

    // verilator lint_off UNUSEDSIGNAL
    logic [25:0] rounded; //low 16 bits intentionally dropped (>> 16)
    //verilator lint_on UNUSEDSIGNAL
    logic [9:0] corr; //round(t * x_lo / 2^16), always < 2^10
    logic [17:0] y_next;
    logic oor_next;

    exp_lut lut (.idx(index), .val(t)); //instantitate table

    always_comb begin
        index = x[17:8];
        x_lo = x[7:0];
        oor_next = (x[18] != x[17]);
        prod = t * x_lo;
        rounded = prod + 26'd32768;
        corr = rounded[25:16];
        y_next = t + {8'd0, corr};
    end

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            out_valid <= 1'b0;
            out_of_range <= 1'b0;
            y <= 18'd0;
        end
        else begin
            out_valid <= in_valid;
            out_of_range <= oor_next;
            y <= y_next;
        end
    end
endmodule: exp_fx
