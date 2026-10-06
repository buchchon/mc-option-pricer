module gaussian_clt (
    input logic clk,
    input logic rst_n, //active low reset
    input logic in_valid, //u is valid in this cycle
    input logic [143:0] u, //12 uniforms x 12 bits, u0 = u[11:0]
    output logic out_valid, // z is valid this cycle
    output logic signed [15:0] z);

    logic [12:0] l1_0, l1_1, l1_2, l1_3, l1_4, l1_5;
    logic [13:0] l2_0, l2_1, l2_2;
    logic [14:0] l3_0;
    logic [15:0] sum;
    logic [15:0] z_next;

    always_comb begin
        l1_0 = u[11:0] + u[23:12];
        l1_1 = u[35:24] + u[47:36];
        l1_2 = u[59:48] + u[71:60];
        l1_3 = u[83:72] + u[95:84];
        l1_4 = u[107:96] + u[119:108];
        l1_5 = u[131:120] + u[143:132];
        
        l2_0 = l1_0 + l1_1;
        l2_1 = l1_2 + l1_3;
        l2_2 = l1_4 + l1_5;

        l3_0 = l2_0 + l2_1;

        sum = l3_0 + {1'b0, l2_2};

        z_next = sum - 16'd24576;
    end

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            out_valid <= 1'b0;
            z <= 16'sd0;
        end
        else begin
            out_valid <= in_valid;
            z <= z_next;
        end
    end
endmodule: gaussian_clt
