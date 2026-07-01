# Session Manager

This layer keeps a session moving in the right order.

For each attempted action, it:

1. Finds the session.
2. Checks the sequence number.
3. Asks the scenario engine for the next state.
4. Runs validation.
5. Writes the ordered log entry.
6. Returns the message the client should see.
