# Domain Extension Suggestions

## Endpoint

`GET /api/v1/domains/suggestions?q=mybrand&extensions=com,net,org,io`

Returns a bounded list of candidate domain names through the same registrar-provider contract used by the domain search endpoint.

## Validation and trust rules

- The brand query must be one valid DNS label, not a URL or full domain.
- Between 1 and 10 extension labels are accepted.
- Duplicate extension labels are removed while preserving order.
- A leading dot is optional in extension values.
- Results currently come from the demo provider and therefore always report availability as `unknown` and source status as `demo_only`.
- This endpoint generates candidates; it does not prove that a domain is available or return live prices.

## Next step

Update the browser form so a bare brand name calls this endpoint and displays candidate extensions. A full domain should continue to call `/api/v1/domains/search`.