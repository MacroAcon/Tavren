# Tavren Examples

This directory contains example code and demonstrations for various Tavren components and workflows.

## Available Examples

### Agent Communication

Demonstrates the communication between agents using the Agent-to-Agent (A2A) and Meaning Context Protocol (MCP) within Tavren's consent-based data exchange framework.

### Data Packaging

Demonstrates the data packaging layer, which securely prepares user data according to consent permissions and buyer trust tiers.

**Features demonstrated:**
- Consent verification and validation
- Multiple anonymization levels based on access requirements
- Trust tier integration for security adjustments
- Data schema validation and formatting
- Time-limited access tokens
- Audit trail generation

To run the data packaging example:

```bash
python examples/data_packaging_example.py
```

Note: This requires a running Tavren backend server.

## Running the Examples

1. Start the Tavren backend server:
   ```bash
   cd tavren-backend
   uvicorn app.main:app --reload
   ```

2. Run the desired example script:
   ```bash
   python examples/data_packaging_example.py
   ```

## Additional Resources

- See the `tavren-backend/app/services/data_packaging.py` file for the full implementation of the data packaging service
- See the `tavren-backend/app/routers/data_packaging.py` file for the API endpoints
- See the `tavren-backend/app/routers/buyer_data.py` file for the buyer-facing API endpoints

## Contents

### A2A + MCP Integration Demo (`a2a_mcp_integration_demo.py`)

This example demonstrates the integration of Google's Agent-to-Agent (A2A) Protocol with Anthropic's Model Context Protocol (MCP) within Tavren's consent-based data exchange framework.

The script simulates:

1. An incoming data request from a buyer agent using the A2A message format
2. Validation of the request against a user's consent preferences
3. Generation of appropriate responses based on consent alignment
4. Alternative suggestions when requests don't align with user preferences

**Key concepts demonstrated:**
- Message structure for agent communication
- Consent preference checking
- Alternative suggestion mechanism
- Full request-response flow

**To run this example:**
```bash
cd examples
python a2a_mcp_integration_demo.py
```

## Integration with Tavren Backend

These examples are intended to serve as reference implementations that can be adapted for integration with the main Tavren backend services. For instance, the A2A + MCP demo could be extended into a full API endpoint in the `tavren-backend/app/routers/agent.py` module.

## Next Steps

Future examples will demonstrate:
- Web frontend visualization of agent exchanges
- Micropayment simulation for data transactions
- Multi-agent conversation flows
- Integration with external LLM providers
