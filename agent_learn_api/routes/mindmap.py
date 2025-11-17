from collections import deque
from flask import Blueprint, request, jsonify
from agent_learn_api.utils.treemap_utils import generate_mindmap, TreeMapNodeList, TreeMapBuilder, TreeMapNode
from agent_learn_api import db
from agent_learn_api.models.treemap import Tree, TreeNode

mindmap_bp = Blueprint("mindmap", __name__)

def _persist_nodes_bfs(tree_id, roots):
    q = deque()
    nodes = []
    for r in roots:
        n = TreeNode(label=r.label, parent_id=None, tree_id=tree_id)
        db.session.add(n)
        db.session.flush()
        nodes.append({"id": n.id, "label": n.label, "parent_id": n.parent_id})
        q.append((r, n.id))
    while q:
        node, parent_id = q.popleft()
        for ch in node.children:
            c = TreeNode(label=ch.label, parent_id=parent_id, tree_id=tree_id)
            db.session.add(c)
            db.session.flush()
            nodes.append({"id": c.id, "label": c.label, "parent_id": c.parent_id})
            q.append((ch, c.id))
    return nodes

@mindmap_bp.route("/", methods=["POST"])
def create_mindmap():
    data = request.get_json(silent=True) or {}
    workspace_id = data.get("workspace_id")
    topic = data.get("topic")
    depth = data.get("depth")
    user_id = data.get("user_id")

    if not workspace_id or not topic or depth is None:
        return jsonify({"error": "Insufficient data"}), 400

    try:
        depth = int(depth)
    except ValueError:
        return jsonify({"error": "Invalid depth"}), 400

    try:
        result = generate_mindmap(topic, topic, depth)
        if isinstance(result, TreeMapNodeList):
            roots = result.contents or []
        else:
            roots = [result.root] if result else []

        if not roots:
            return jsonify({"error": "Empty mindmap"}), 422

        # Safe transaction block
        with db.session.begin_nested():
            tree = Tree(workspace_id=workspace_id, user_id=user_id, name=topic)
            db.session.add(tree)
            db.session.flush()
            nodes = _persist_nodes_bfs(tree.id, roots)
        db.session.commit()

        return jsonify({
            "tree_id": tree.id,
            "name": tree.name,
            "workspace_id": tree.workspace_id,
            "user_id": tree.user_id,
            "nodes_count": len(nodes),
            "tree_dict": result.show() if hasattr(result, "show") else {}
        }), 201

    except Exception as e:
        db.session.rollback()
        print("❌ Mindmap creation failed:", e)
        return jsonify({"error": "Failed to create mindmap", "details": str(e)}), 500

    
@mindmap_bp.route("/<int:workspace_id>", methods=["GET"])
def get_mindmaps(workspace_id):
    trees = Tree.query.filter_by(workspace_id=workspace_id).all()
    out = []
    for tree in trees:
        nodes = TreeNode.query.filter_by(tree_id=tree.id).order_by(TreeNode.id).all()
        # Reconstruct to TreeMapBuilder
        builder = TreeMapBuilder()
        root = None
        
        if nodes:
            id_to_tm = {n.id: TreeMapNode(label=n.label) for n in nodes}
            for n in nodes:
                if n.parent_id is None:
                    root = id_to_tm[n.id]
                else:
                    p = id_to_tm.get(n.parent_id)
                    if p:
                        p.children.append(id_to_tm[n.id])
            if root:
                builder.add_root(root)
        out.append({
            "tree_id": tree.id,
            "name": tree.name,
            "workspace_id": tree.workspace_id,
            "user_id": tree.user_id,
            "nodes_count": len(nodes),
            "tree_dict": builder.show() if builder.root else None
        })
    return jsonify({"workspace_id": workspace_id, "count": len(out), "trees": out}), 200

@mindmap_bp.route("/<int:tree_id>", methods=["DELETE"])
def delete_tree(tree_id):
    tree = Tree.query.get(tree_id)
    if not tree:
        return jsonify({"error": f"Tree {tree_id} not found"}), 404

    db.session.delete(tree)
    db.session.commit()
    return jsonify({"message": f"Tree {tree} deleted"}), 200       