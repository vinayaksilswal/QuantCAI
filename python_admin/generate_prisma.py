import os
import re

# 1. Read the original schema
with open("../prisma/schema.prisma", "r") as f:
    content = f.read()

# 2. Inject url into datasource if not present
if "url =" not in content and "url  =" not in content:
    content = content.replace(
        'provider = "postgresql"',
        'provider = "postgresql"\n  url      = env("DATABASE_URL")'
    )

# 2.5 Remove generator client block (for js)
content = re.sub(r'generator client\s*\{[^}]+\}', '', content)

# 3. Append the python generator
python_generator = """
generator py {
  provider             = "prisma-client-py"
  recursive_type_depth = 5
}
"""
if "generator py" not in content:
    content += python_generator

# 4. Write to a temporary schema file
with open("schema_py.prisma", "w") as f:
    f.write(content)
print("Created schema_py.prisma with url injected and JS generator removed")
