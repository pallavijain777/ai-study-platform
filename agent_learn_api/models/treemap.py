from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship, backref
from agent_learn_api import db  # assuming SQLAlchemy() instance


class Tree(db.Model):
    __tablename__ = "trees"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    user_id = Column(Integer, nullable=True)
    workspace_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

    # purely acts as a register of which nodes belong to it
    nodes = relationship(
        "TreeNode",
        back_populates="tree",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<Tree id={self.id} name='{self.name}'>"


class TreeNode(db.Model):
    __tablename__ = "tree_nodes"

    id = Column(Integer, primary_key=True)
    label = Column(String(255), nullable=False)

    # Hierarchy references
    parent_id = Column(Integer, ForeignKey("tree_nodes.id", ondelete="CASCADE"), nullable=True)
    tree_id = Column(Integer, ForeignKey("trees.id", ondelete="CASCADE"), nullable=False)

    # relationships
    tree = relationship("Tree", back_populates="nodes")
    children = relationship(
        "TreeNode",
        backref=backref("parent", remote_side=[id]),
        cascade="all, delete-orphan"
    )

    created_at = Column(DateTime, default=datetime.now(timezone.utc))

    def __repr__(self):
        return f"<TreeNode id={self.id} label='{self.label}' parent_id={self.parent_id}>"
