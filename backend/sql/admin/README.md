# 数据库管理员脚本

目录：`backend/sql/admin`

## 脚本说明

1. `001_create_roles.sql`
创建组角色和登录用户：
- `grp_annotation_ddl`
- `grp_annotation_rw`
- `grp_annotation_ro`
- `annotation_migrator`
- `annotation_app`
- `annotation_readonly`

2. `002_grant_annotation_platform.sql`
为 `annotation_platform` 授权数据库连接、schema、表、序列权限。

3. `003_default_privileges.sql`
配置默认权限，保证 `annotation_migrator` 新建对象自动授权给运行账号。

## 执行顺序

按 `001 -> 002 -> 003` 顺序执行。

## 执行示例（PowerShell）

```powershell
$env:PGCLIENTENCODING = "UTF8"

$MIGRATOR_PWD = Read-Host "Input migrator password" -AsSecureString
$APP_PWD = Read-Host "Input app password" -AsSecureString
$RO_PWD = Read-Host "Input readonly password" -AsSecureString

# 将 SecureString 转普通字符串，仅用于当前会话命令参数
$MIGRATOR_PLAIN = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($MIGRATOR_PWD))
$APP_PLAIN = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($APP_PWD))
$RO_PLAIN = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($RO_PWD))

psql -U postgres -d postgres -v migrator_password="$MIGRATOR_PLAIN" -v app_password="$APP_PLAIN" -v readonly_password="$RO_PLAIN" -f backend\sql\admin\001_create_roles.sql
psql -U postgres -d annotation_platform -f backend\sql\admin\002_grant_annotation_platform.sql
psql -U postgres -d annotation_platform -f backend\sql\admin\003_default_privileges.sql
```

## 注意事项

- `001_create_roles.sql` 不内置默认密码，必须通过 `-v` 参数传入。
- 请使用强密码，建议长度至少 16，包含大小写字母、数字和特殊字符。
- 建议使用 PostgreSQL 10+ 的 `psql`（脚本用到了 `\if` 和 `\gexec`）。
- 这些脚本属于运维初始化，不替代 Alembic migration。
- 数据库 schema 变更仍需走 `alembic/`。
