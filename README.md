# Raspberry Pi GPIO Communication

A small experiment with a custom asynchronous protocol to send data through a single wire (alike UART).

For testing, I was using two RPi Zero w 1.1, and could not go much higher than 80bps, which was way more than I originally anticipated.

# Running

The default GPIO ports are:

| role   | port |
| ------ | ---- |
| input  | 29   |
| output | 31   |

So the two connected RPi's should have these ports cross-wired so that the I/O of one is the O/I of the other.

Run main.py with a 'b' argument on the one that is going receive the message, and do the same with 'a' on the one that is going to receive it. Now you may type a message and it should be sent to the connected device.