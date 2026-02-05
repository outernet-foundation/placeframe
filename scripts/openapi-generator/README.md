## Creating a new template patch

This repo stores OpenAPI Generator template changes as `.patch` files.

To create a new patch, edit the relevant mustache template in-place under:

`scripts/openapi-generator/templates-generated/...`

Then run:

```bash
git diff -- scripts/openapi-generator/templates-generated \
  > scripts/openapi-generator/templates-patches/csharp/000X-your-patch-name.patch
```

And then rerun codegen and commit. I you want to create multiple separate patch files, you must commit each patch before creating the next one for the above `git diff` command to do the right thing.
