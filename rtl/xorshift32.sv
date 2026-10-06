module xorshift32 (
    input logic clk,
    input logic rst_n, //active low reset
    input logic en, //advance one step when high
    input logic [31:0] seed, //initial state, must be nonzero
    output logic [31:0] out);

    logic [31:0] state;
    logic [31:0] s1, s2, s3; //result of 3 xor shifts

    always_comb begin
        s1 = state ^ (state << 13);
        s2 = s1 ^ (s1 >> 17);
        s3 = s2 ^ (s2 << 5);
    end

    always_ff @(posedge clk) begin
        if (!rst_n) begin
            state <= seed;
        end
        else if (en) begin
            state <= s3;
        end
    end

    assign out = state;
endmodule: xorshift32
