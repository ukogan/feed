# Existing Tools Landscape

## Tools to reference (don't rebuild)

| Tool | Stars | What it does | How we use it |
|------|-------|-------------|---------------|
| [sodapy](https://github.com/afeld/sodapy) | 427 | Python Socrata/SODA API client | Reference in SCO skill as the recommended query library |
| [socrata/odp-mcp](https://github.com/socrata/odp-mcp) | 1 | Official Socrata MCP server | Could use directly for bythenumbers.sco.ca.gov queries |
| [django-calaccess](https://github.com/palewire/django-calaccess-raw-data) | 65 | CA campaign finance ETL (Django) | Reference for CAL-ACCESS data model, don't use Django dependency |
| [OpenPoliceData](https://github.com/openpolicedata/openpolicedata) | 49 | Police data across 236 agencies | Use for RIPA stops data, supplement DOJ crime skill |
| [lzinga/us-gov-open-data-mcp](https://github.com/lzinga/us-gov-open-data-mcp) | 91 | 300+ federal gov API tools | Reference pattern for MCP server design |

## Gaps we fill (novel work)

| Gap | Status | Notes |
|-----|--------|-------|
| CA state-level MCP server | No one has built this | First in any MCP registry |
| TRA-to-jurisdiction mapping | No tool exists | Genuinely novel |
| SACS school finance parser | No tool exists | CDE data is Excel/DAT, unparsed |
| CalPERS/CalSTRS data access | No tool exists | Completely open space |
| CAASPP test score wrapper | No tool exists | Bulk CSV, needs parsing |
| "Where does my property tax go" | typpo/ca-property-tax (inactive, no TRA breakdown) | Our core product concept |
| State-level budget normalization | No tool exists | Cross-jurisdiction comparison |
| Citizen query translation | No tool exists | NLP to data source routing |

## MCP ecosystem context

- 13,230+ MCP servers listed on PulseMCP
- Federal gov data: 5+ MCP servers (USAspending, Congress, SEC, FDA, etc.)
- State/local gov data: 0 MCP servers
- The Socrata MCP is generic (any portal) but has no CA-specific context
- No Claude Code skill repositories include government/civic data
