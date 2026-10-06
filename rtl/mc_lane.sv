module mc_lane (
    input logic clk,
    input logic rst_n, //active low reset
    input logic start, //1 cycle pulse, begin and then run
    input logic [31:0] n_paths, //paths to simulate
    input logic [191:0] seeds, //6 x 32 bit rng seeds that are nonzero
    input logic signed [23:0] a, //(r - sigma^2/2)T, signed Q3.20
    input logic signed [23:0] b, //sigma*sqrt(T), signed Q3.20
    input logic [17:0] s0, //stock price, Q10.8
    input logic [17:0] k, //strike price, Q10.8
    output logic done, //all paths have been accumulated
    output logic [47:0] sum, //sum of payoffs Q40.8
    output logic oor_seen); //any x out of exp range

    //control
    logic active;
    logic [31:0] issued, added;
    logic issue; //send new path into pipeline this cycle
    logic rng_rst_n; //start also reloads all the seeds

    assign issue = active && (issued != n_paths);
    assign rng_rst_n = rst_n && !start;
    assign done = active && (added == n_paths);

    //stage 0: 6 random num generator into 12 uniform

    //verilator lint_off UNUSEDSIGNAL
    logic [31:0] r0, r1, r2, r3, r4, r5; //low 8 bits of each rng unused
    //verilator lint_on UNUSEDSIGNAL
    xorshift32 rng0 (.clk(clk), .rst_n(rng_rst_n), .en(issue), 
                     .seed(seeds[31:0]), .out(r0));
    xorshift32 rng1 (.clk(clk), .rst_n(rng_rst_n), .en(issue), 
                     .seed(seeds[63:32]), .out(r1));
    xorshift32 rng2 (.clk(clk), .rst_n(rng_rst_n), .en(issue), 
                     .seed(seeds[95:64]), .out(r2));
    xorshift32 rng3 (.clk(clk), .rst_n(rng_rst_n), .en(issue), 
                     .seed(seeds[127:96]), .out(r3));
    xorshift32 rng4 (.clk(clk), .rst_n(rng_rst_n), .en(issue), 
                     .seed(seeds[159:128]), .out(r4));
    xorshift32 rng5 (.clk(clk), .rst_n(rng_rst_n), .en(issue), 
                     .seed(seeds[191:160]), .out(r5));
    
    logic [143:0] u; //u0 = r0[31:20] in bits 11:0, u1 = r0[19:8], ...
    assign u = {r5[19:8], r5[31:20], r4[19:8], r4[31:20], r3[19:8], r3[31:20],
                r2[19:8], r2[31:20], r1[19:8], r1[31:20], r0[19:8], r0[31:20]};

    //stage 1: gaussian
    logic z_valid;
    logic signed [15:0] z;
    gaussian_clt gauss (.clk(clk), .rst_n(rst_n), .in_valid(issue), .u(u),
                        .out_valid(z_valid), .z(z));
    
    //stage 2: x = a + b * z
    logic signed [39:0] bz, a_ext, x_sum;
    //verilator lint_off UNUSEDSIGNAL
    logic signed [39:0] x_rnd; //only bits [34:16] kept
    //verilator lint_on UNUSEDSIGNAL
    logic signed [18:0] x;
    logic x_valid;
    always_comb begin
        bz = b * z;
        a_ext = {{4{a[23]}}, a, 12'd0};
        x_sum = a_ext + bz;
        x_rnd = x_sum + 40'sd32768;
    end
    always_ff @(posedge clk) begin
        if (!rst_n) begin
            x_valid <= 1'b0;
            x <= 19'sd0;
        end
        else begin
            x_valid <= z_valid; 
            x <= x_rnd[34:16];
        end
    end

    //stage 3: exp
    logic e_valid, e_oor;
    logic [17:0] e;
    exp_fx expu (.clk(clk), .rst_n(rst_n), .in_valid(x_valid), .x(x),
                 .out_valid(e_valid), .out_of_range(e_oor), .y(e));
    
    //stage 4a: S_T = S0 * e, rounded, then registered
    logic [35:0] s_prod;
    //verilator lint_off UNUSEDSIGNAL
    logic [35:0] s_rnd; //only bits [35:15] kept
    //verilator lint_on UNUSEDSIGNAL
    logic [20:0] s_t, s_t_q;
    logic s_valid;
    always_comb begin
        s_prod = s0 * e;
        s_rnd = s_prod + 36'd16384; //round + half LSB
        s_t = s_rnd[35:15];
    end
    always_ff @(posedge clk) begin 
        if (!rst_n) begin
            s_valid <= 1'b0;
            s_t_q <= 21'd0;
        end
        else begin
            s_valid <= e_valid;
            s_t_q <= s_t;
        end
    end

    //stage 4b: payoff = max(S_T - K, 0)
    logic [20:0] payoff_next, payoff;
    logic p_valid;
    always_comb begin
        if (s_t_q > {3'd0, k}) begin
            payoff_next = s_t_q - {3'd0, k};
        end
        else begin
            payoff_next = 21'd0;
        end
    end
    always_ff @(posedge clk) begin
        if (!rst_n) begin
            p_valid <= 1'b0;
            payoff <= 21'd0;
        end
        else begin
            p_valid <= s_valid;
            payoff <= payoff_next;
        end
    end

    //stage 5: accumulate + control
    always_ff @(posedge clk) begin
        if (!rst_n) begin
            active   <= 1'b0;
            issued   <= 32'd0;
            added    <= 32'd0;
            sum      <= 48'd0;
            oor_seen <= 1'b0;
        end
        else if (start) begin
            active   <= 1'b1;
            issued   <= 32'd0;
            added    <= 32'd0;
            sum      <= 48'd0;
            oor_seen <= 1'b0;
        end
        else begin
            if (issue)
                issued <= issued + 32'd1;
            if (p_valid) begin
                added <= added + 32'd1;
                sum   <= sum + {27'd0, payoff};
            end
            if (e_valid && e_oor)
                oor_seen <= 1'b1;
        end
    end
endmodule: mc_lane




