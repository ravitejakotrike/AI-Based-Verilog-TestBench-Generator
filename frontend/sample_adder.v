// Sample 4-bit full adder module
// Use this file to test the testbench generator
module adder (
    input  [3:0] a,
    input  [3:0] b,
    input        cin,
    output [3:0] sum,
    output       cout
);
    wire [4:0] result;
    assign result = a + b + cin;
    assign sum   = result[3:0];
    assign cout  = result[4];
endmodule
