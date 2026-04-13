"""
Git 版本控制工具模块

提供 Git 仓库操作和版本管理功能，包括：
- 获取最新提交记录
- 创建新分支
- 合并分支
- 查看提交历史
- 获取代码差异

注：本模块使用模拟数据演示功能，生产环境中需集成真实 Git 仓库 API。
"""

import json
import random
import logging
from datetime import datetime, timedelta
from typing import Optional

from crewai.tools import tool

logger = logging.getLogger(__name__)

# 模拟 Git 仓库信息
MOCK_REPO = {
    "name": "devops-app",
    "remote_url": "https://github.com/company/devops-app.git",
    "default_branch": "main",
    "current_branch": "main",
}

# 模拟提交历史
MOCK_COMMITS = [
    {
        "sha": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
        "short_sha": "a1b2c3d",
        "message": "feat: 添加数据库连接池配置优化",
        "author": "张三",
        "email": "zhangsan@company.com",
        "date": "2026-04-13T06:30:00",
        "branch": "main",
        "tags": ["v2.1.0"],
        "files_changed": 3,
        "insertions": 45,
        "deletions": 12,
        "files": ["src/config/database.py", "src/models/base.py", "tests/test_db.py"],
    },
    {
        "sha": "b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3",
        "short_sha": "b2c3d4e",
        "message": "fix: 修复订单查询 N+1 问题",
        "author": "李四",
        "email": "lisi@company.com",
        "date": "2026-04-12T15:20:00",
        "branch": "main",
        "tags": [],
        "files_changed": 2,
        "insertions": 23,
        "deletions": 8,
        "files": ["src/api/orders.py", "tests/test_orders.py"],
    },
    {
        "sha": "c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4",
        "short_sha": "c3d4e5f",
        "message": "chore: 更新 Docker 基础镜像到 python:3.11",
        "author": "王五",
        "email": "wangwu@company.com",
        "date": "2026-04-12T10:00:00",
        "branch": "main",
        "tags": [],
        "files_changed": 1,
        "insertions": 3,
        "deletions": 3,
        "files": ["Dockerfile"],
    },
    {
        "sha": "d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5",
        "short_sha": "d4e5f6a",
        "message": "feat: 实现用户认证中间件",
        "author": "赵六",
        "email": "zhaoliu@company.com",
        "date": "2026-04-11T16:45:00",
        "branch": "main",
        "tags": ["v2.0.0"],
        "files_changed": 5,
        "insertions": 128,
        "deletions": 34,
        "files": [
            "src/middleware/auth.py",
            "src/config/jwt.py",
            "src/api/users.py",
            "tests/test_auth.py",
            "README.md",
        ],
    },
    {
        "sha": "e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6",
        "short_sha": "e5f6a1b",
        "message": "fix: 修复内存泄漏问题（缓存未及时清理）",
        "author": "张三",
        "email": "zhangsan@company.com",
        "date": "2026-04-11T09:30:00",
        "branch": "main",
        "tags": [],
        "files_changed": 2,
        "insertions": 15,
        "deletions": 5,
        "files": ["src/cache/manager.py", "tests/test_cache.py"],
    },
    {
        "sha": "f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1",
        "short_sha": "f6a1b2c",
        "message": "docs: 更新 API 文档和部署说明",
        "author": "钱七",
        "email": "qianqi@company.com",
        "date": "2026-04-10T14:00:00",
        "branch": "main",
        "tags": [],
        "files_changed": 3,
        "insertions": 85,
        "deletions": 20,
        "files": ["docs/api.md", "docs/deployment.md", "README.md"],
    },
]

# 模拟分支列表
MOCK_BRANCHES = [
    {"name": "main", "is_default": True, "last_commit": "a1b2c3d", "is_protected": True},
    {"name": "develop", "is_default": False, "last_commit": "b2c3d4e", "is_protected": False},
    {"name": "feature/db-optimization", "is_default": False, "last_commit": "c3d4e5f", "is_protected": False},
    {"name": "hotfix/memory-leak", "is_default": False, "last_commit": "e5f6a1b", "is_protected": False},
    {"name": "release/v2.1.0", "is_default": False, "last_commit": "a1b2c3d", "is_protected": True},
]

# 模拟代码差异
MOCK_DIFFS = {
    "src/config/database.py": """diff --git a/src/config/database.py b/src/config/database.py
--- a/src/config/database.py
+++ b/src/config/database.py
@@ -15,7 +15,15 @@ from sqlalchemy import create_engine
 DATABASE_URL = os.getenv("DATABASE_URL", "mysql://localhost/appdb")
 
-engine = create_engine(DATABASE_URL, pool_size=5, max_overflow=10)
+engine = create_engine(
+    DATABASE_URL,
+    pool_size=20,          # 从5增加到20以支持更高并发
+    max_overflow=30,       # 允许额外30个临时连接
+    pool_timeout=30,       # 等待连接超时30秒
+    pool_recycle=3600,     # 每小时回收连接防止超时断开
+    pool_pre_ping=True,    # 使用前检查连接是否有效
+    echo=False,
+)
 
 SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
""",
    "src/api/orders.py": """diff --git a/src/api/orders.py b/src/api/orders.py
--- a/src/api/orders.py
+++ b/src/api/orders.py
@@ -32,12 +32,8 @@ def get_orders(user_id: int, db: Session):
     orders = db.query(Order).filter(Order.user_id == user_id).all()
-    result = []
-    for order in orders:
-        items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
-        result.append({**order.__dict__, "items": items})
-    return result
+    # 使用 joinedload 避免 N+1 查询问题
+    orders = db.query(Order).options(
+        joinedload(Order.items)
+    ).filter(Order.user_id == user_id).all()
+    return orders
""",
}


@tool("get_latest_commits")
def get_latest_commits(branch: str = "main", count: int = 5) -> str:
    """
    获取指定分支的最新提交记录。

    Args:
        branch: 分支名称（默认 'main'）
        count: 获取的提交数量（默认5）

    Returns:
        JSON 格式的提交记录列表
    """
    logger.info("获取最新提交: branch='%s', count=%d", branch, count)

    # 验证分支是否存在
    branch_names = [b["name"] for b in MOCK_BRANCHES]
    if branch not in branch_names:
        return json.dumps(
            {
                "error": f"分支 '{branch}' 不存在",
                "available_branches": branch_names,
            },
            ensure_ascii=False,
        )

    commits = MOCK_COMMITS[:count]

    result = {
        "repository": MOCK_REPO["name"],
        "branch": branch,
        "total_shown": len(commits),
        "commits": [
            {
                "sha": c["short_sha"],
                "message": c["message"],
                "author": c["author"],
                "date": c["date"],
                "files_changed": c["files_changed"],
                "changes": f"+{c['insertions']}/-{c['deletions']}",
                "tags": c["tags"],
            }
            for c in commits
        ],
    }

    return json.dumps(result, ensure_ascii=False, indent=2)


@tool("create_branch")
def create_branch(
    branch_name: str,
    from_branch: str = "main",
    description: Optional[str] = None,
) -> str:
    """
    创建新的 Git 分支。

    Args:
        branch_name: 新分支名称（建议格式：feature/xxx 或 hotfix/xxx）
        from_branch: 基于哪个分支创建（默认 'main'）
        description: 分支描述（可选）

    Returns:
        JSON 格式的创建结果
    """
    logger.info("创建分支: %s (来自 %s)", branch_name, from_branch)

    # 验证来源分支
    branch_names = [b["name"] for b in MOCK_BRANCHES]
    if from_branch not in branch_names:
        return json.dumps(
            {"success": False, "error": f"来源分支 '{from_branch}' 不存在"},
            ensure_ascii=False,
        )

    # 检查分支名是否合法
    import re
    if not re.match(r"^[a-zA-Z0-9/_\-\.]+$", branch_name):
        return json.dumps(
            {"success": False, "error": f"分支名 '{branch_name}' 包含非法字符"},
            ensure_ascii=False,
        )

    # 获取来源分支的最新提交
    base_commit = MOCK_COMMITS[0]

    result = {
        "success": True,
        "branch_name": branch_name,
        "from_branch": from_branch,
        "base_commit": base_commit["short_sha"],
        "base_commit_message": base_commit["message"],
        "description": description,
        "created_at": datetime.now().isoformat(),
        "remote_url": f"{MOCK_REPO['remote_url'].replace('.git', '')}/tree/{branch_name}",
        "message": f"分支 '{branch_name}' 已从 '{from_branch}' 创建成功",
        "next_steps": [
            f"git checkout {branch_name}",
            "# 进行你的更改",
            "git add . && git commit -m '你的提交信息'",
            f"git push origin {branch_name}",
        ],
    }

    return json.dumps(result, ensure_ascii=False, indent=2)


@tool("merge_branch")
def merge_branch(
    source_branch: str,
    target_branch: str = "main",
    merge_message: Optional[str] = None,
) -> str:
    """
    将源分支合并到目标分支。

    Args:
        source_branch: 要合并的源分支
        target_branch: 目标分支（默认 'main'）
        merge_message: 合并提交信息（可选）

    Returns:
        JSON 格式的合并结果
    """
    logger.info("合并分支: %s -> %s", source_branch, target_branch)

    # 验证分支
    branch_names = [b["name"] for b in MOCK_BRANCHES]
    if source_branch not in branch_names:
        return json.dumps(
            {"success": False, "error": f"源分支 '{source_branch}' 不存在"},
            ensure_ascii=False,
        )
    if target_branch not in branch_names:
        return json.dumps(
            {"success": False, "error": f"目标分支 '{target_branch}' 不存在"},
            ensure_ascii=False,
        )

    # 检查目标分支是否受保护（需要 PR 合并）
    target = next(b for b in MOCK_BRANCHES if b["name"] == target_branch)
    if target.get("is_protected"):
        return json.dumps(
            {
                "success": False,
                "error": f"分支 '{target_branch}' 受保护，需要通过 Pull Request 合并",
                "pr_url": f"{MOCK_REPO['remote_url'].replace('.git', '')}/compare/{target_branch}...{source_branch}",
            },
            ensure_ascii=False,
        )

    # 模拟合并结果
    merge_commit_sha = "".join(random.choices("0123456789abcdef", k=7))
    merge_msg = merge_message or f"Merge branch '{source_branch}' into {target_branch}"

    result = {
        "success": True,
        "source_branch": source_branch,
        "target_branch": target_branch,
        "merge_commit": merge_commit_sha,
        "merge_message": merge_msg,
        "conflicts": False,
        "files_merged": 3,
        "stats": {"insertions": 45, "deletions": 12, "files": 3},
        "merged_at": datetime.now().isoformat(),
        "message": f"分支 '{source_branch}' 已成功合并到 '{target_branch}'",
    }

    return json.dumps(result, ensure_ascii=False, indent=2)


@tool("get_commit_history")
def get_commit_history(
    branch: str = "main",
    author: Optional[str] = None,
    since_days: int = 7,
    page: int = 1,
    per_page: int = 10,
) -> str:
    """
    获取提交历史记录。

    Args:
        branch: 分支名称（默认 'main'）
        author: 按作者过滤（可选）
        since_days: 查看最近N天的提交（默认7天）
        page: 页码（默认1）
        per_page: 每页条数（默认10）

    Returns:
        JSON 格式的提交历史
    """
    logger.info(
        "获取提交历史: branch='%s', author='%s', 最近%d天", branch, author, since_days
    )

    commits = MOCK_COMMITS

    # 按作者过滤
    if author:
        commits = [c for c in commits if author in c["author"] or author in c["email"]]

    # 分页
    total = len(commits)
    start = (page - 1) * per_page
    end = start + per_page
    page_commits = commits[start:end]

    result = {
        "repository": MOCK_REPO["name"],
        "branch": branch,
        "author_filter": author,
        "period": f"最近 {since_days} 天",
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": (total + per_page - 1) // per_page,
        },
        "commits": page_commits,
        "statistics": {
            "total_commits": total,
            "unique_authors": len({c["author"] for c in MOCK_COMMITS}),
            "files_changed": sum(c["files_changed"] for c in commits),
            "total_insertions": sum(c["insertions"] for c in commits),
            "total_deletions": sum(c["deletions"] for c in commits),
        },
    }

    return json.dumps(result, ensure_ascii=False, indent=2)


@tool("get_diff")
def get_diff(
    commit_sha: Optional[str] = None,
    file_path: Optional[str] = None,
    base_branch: str = "main",
    compare_branch: Optional[str] = None,
) -> str:
    """
    获取代码差异信息。

    Args:
        commit_sha: 提交 SHA（可选，查看特定提交的变更）
        file_path: 文件路径（可选，查看特定文件的差异）
        base_branch: 基准分支（默认 'main'）
        compare_branch: 对比分支（可选）

    Returns:
        代码差异内容
    """
    logger.info(
        "获取代码差异: commit='%s', file='%s'", commit_sha, file_path
    )

    if commit_sha:
        # 查找特定提交
        commit = next(
            (c for c in MOCK_COMMITS if c["sha"].startswith(commit_sha) or c["short_sha"] == commit_sha),
            None,
        )
        if not commit:
            return json.dumps(
                {"error": f"未找到提交 '{commit_sha}'"},
                ensure_ascii=False,
            )

        result = {
            "commit": commit["short_sha"],
            "message": commit["message"],
            "author": commit["author"],
            "date": commit["date"],
            "files_changed": commit["files_changed"],
            "stats": {
                "insertions": commit["insertions"],
                "deletions": commit["deletions"],
            },
            "changed_files": commit["files"],
            "diff": MOCK_DIFFS.get(commit["files"][0], "# 差异内容（模拟数据）\n+ 新增代码行\n- 删除代码行"),
        }
    else:
        # 查看所有差异
        diffs = []
        for file_path_key, diff_content in MOCK_DIFFS.items():
            if file_path and file_path not in file_path_key:
                continue
            diffs.append({
                "file": file_path_key,
                "diff": diff_content,
            })

        result = {
            "base": base_branch,
            "compare": compare_branch or "working-directory",
            "files": diffs,
            "total_files": len(diffs),
        }

    return json.dumps(result, ensure_ascii=False, indent=2)
