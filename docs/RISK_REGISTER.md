# Risk Register

See [PM Delivery Artifacts](PM_DELIVERY_ARTIFACTS.md) for the full source pack.

| Risk | Probability | Impact | Mitigation |
|---|---:|---:|---|
| Runway queue latency | High | High | Pre-generate fallback assets and poll asynchronously |
| Content moderation flag | Medium | High | Generic abstract visuals, no brands, no real faces |
| Telegram delivery failure | Low | Medium | Fallback to poster plus landing link |
| Video stitching failure | Medium | High | Simple concat first, re-encode fallback |
| Missed scope | High | High | Preserve end-to-end hero path, cut secondary UI |

