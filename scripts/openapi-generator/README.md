## Creating a new template patch

This repo stores OpenAPI Generator template changes as `.patch` files.

To create a new patch, edit the relevant mustache template in-place under:

`scripts/openapi-generator/templates-generated/...`

Then run:

```bash
git diff -- scripts/openapi-generator/templates-generated \
  > scripts/openapi-generator/template-patches/csharp/000X-your-patch-name.patch
```
