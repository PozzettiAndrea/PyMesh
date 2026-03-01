"""
Generate visual demo of PyMesh for GitHub Pages.

Shows boolean operations, mesh repair, self-intersection resolution,
and remeshing — each with the actual Python code alongside before/after renders.
"""

import os
import shutil
import time
import textwrap
import numpy as np

import pyvista as pv

pv.OFF_SCREEN = True

import pymesh

OUT_DIR = os.path.join(os.path.dirname(__file__), "_site")

# Dark theme
BG_COLOR = "#1a1a2e"
MESH_COLOR_IN = "#4fc3f7"
MESH_COLOR_OUT = "#81c784"
MESH_COLOR_B = "#ffb74d"
EDGE_COLOR = "#222244"
TEXT_COLOR = "#e0e0e0"


def pv_from_pymesh(mesh):
    """Convert PyMesh mesh to PyVista PolyData."""
    verts = mesh.vertices
    faces = mesh.faces
    n = len(faces)
    pv_faces = np.column_stack([np.full(n, 3, dtype=np.int32), faces]).ravel()
    return pv.PolyData(verts, pv_faces)


def render_mesh(mesh, filename, title, color=MESH_COLOR_IN,
                window_size=(800, 600)):
    pl = pv.Plotter(off_screen=True, window_size=window_size)
    if mesh.n_points > 0:
        pl.add_mesh(mesh, color=color, show_edges=True, edge_color=EDGE_COLOR,
                    line_width=0.5, lighting=True, smooth_shading=True)
    pl.add_text(title, position="upper_left", font_size=12, color=TEXT_COLOR)
    pl.set_background(BG_COLOR)
    pl.camera_position = "iso"
    pl.screenshot(filename, transparent_background=False)
    pl.close()


def render_two_meshes(mesh_a, mesh_b, filename, title,
                      color_a=MESH_COLOR_IN, color_b=MESH_COLOR_B,
                      window_size=(800, 600)):
    """Render two meshes in the same scene."""
    pl = pv.Plotter(off_screen=True, window_size=window_size)
    pl.add_mesh(mesh_a, color=color_a, show_edges=True, edge_color=EDGE_COLOR,
                line_width=0.5, lighting=True, smooth_shading=True, opacity=0.6)
    pl.add_mesh(mesh_b, color=color_b, show_edges=True, edge_color=EDGE_COLOR,
                line_width=0.5, lighting=True, smooth_shading=True, opacity=0.6)
    pl.add_text(title, position="upper_left", font_size=12, color=TEXT_COLOR)
    pl.set_background(BG_COLOR)
    pl.camera_position = "iso"
    pl.screenshot(filename, transparent_background=False)
    pl.close()


def html_escape(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


TEMPLATE_DIR = os.path.dirname(__file__)


def _render_demo(d):
    code_html = html_escape(d["code"])
    label = d.get("after_label", "Output")
    return f"""
    <section class="demo">
      <div class="demo-grid">
        <div class="demo-code">
          <pre><code>{code_html}</code></pre>
          <p class="timing">{d['elapsed']:.2f}s &mdash; {d['verts_in']:,} &rarr; {d['verts_out']:,} verts, {d['faces_in']:,} &rarr; {d['faces_out']:,} faces</p>
        </div>
        <div class="demo-images">
          <div class="comparison">
            <div class="panel">
              <img src="{d['name']}_before.png" alt="Before">
              <span class="label">Input</span>
            </div>
            <div class="panel">
              <img src="{d['name']}_after.png" alt="After">
              <span class="label">{label}</span>
            </div>
          </div>
        </div>
      </div>
    </section>"""


def generate_html(sections):
    sections_html = ""
    for section in sections:
        sections_html += f"""
    <h2 class="section-title">{section['title']}</h2>
    <p class="section-sub">{section['subtitle']}</p>"""
        for d in section["demos"]:
            sections_html += _render_demo(d)

    with open(os.path.join(TEMPLATE_DIR, "template.html")) as f:
        template = f.read()

    html = template.replace("{{sections}}", sections_html)

    with open(os.path.join(OUT_DIR, "index.html"), "w") as f:
        f.write(html)


def make_box(lo, hi):
    """Create a box mesh via PyMesh."""
    return pymesh.generate_box_mesh(np.array(lo), np.array(hi))


def main():
    if os.path.exists(OUT_DIR):
        shutil.rmtree(OUT_DIR)
    os.makedirs(OUT_DIR)

    sections = []

    # ── Boolean Operations ─────────────────────────────────────────
    bool_demos = []

    box_a = make_box([0, 0, 0], [1, 1, 1])
    box_b = make_box([0.5, 0.5, 0.5], [1.5, 1.5, 1.5])

    pv_a = pv_from_pymesh(box_a)
    pv_b = pv_from_pymesh(box_b)

    # Render inputs (two overlapping boxes)
    render_two_meshes(
        pv_a, pv_b,
        os.path.join(OUT_DIR, "bool_union_before.png"),
        f"Inputs: {box_a.num_vertices}+{box_b.num_vertices} verts")

    render_two_meshes(
        pv_a, pv_b,
        os.path.join(OUT_DIR, "bool_intersection_before.png"),
        f"Inputs: {box_a.num_vertices}+{box_b.num_vertices} verts")

    render_two_meshes(
        pv_a, pv_b,
        os.path.join(OUT_DIR, "bool_difference_before.png"),
        f"Inputs: {box_a.num_vertices}+{box_b.num_vertices} verts")

    for op in ["union", "intersection", "difference"]:
        t0 = time.perf_counter()
        result = pymesh.boolean(box_a, box_b, op, engine="igl")
        elapsed = time.perf_counter() - t0

        pv_result = pv_from_pymesh(result)
        render_mesh(
            pv_result,
            os.path.join(OUT_DIR, f"bool_{op}_after.png"),
            f"{op.title()}: {result.num_vertices} verts, {result.num_faces} faces  ({elapsed:.2f}s)",
            color=MESH_COLOR_OUT)

        bool_demos.append({
            "name": f"bool_{op}",
            "verts_in": box_a.num_vertices + box_b.num_vertices,
            "faces_in": box_a.num_faces + box_b.num_faces,
            "verts_out": result.num_vertices,
            "faces_out": result.num_faces,
            "elapsed": elapsed,
            "code": textwrap.dedent(f"""\
                import pymesh
                import numpy as np

                box_a = pymesh.generate_box_mesh(
                    np.array([0, 0, 0]),
                    np.array([1, 1, 1]))
                box_b = pymesh.generate_box_mesh(
                    np.array([0.5, 0.5, 0.5]),
                    np.array([1.5, 1.5, 1.5]))

                result = pymesh.boolean(
                    box_a, box_b, "{op}",
                    engine="igl")"""),
            "after_label": op.title(),
        })

    sections.append({
        "title": "Boolean Operations",
        "subtitle": "CSG union, intersection, and difference via IGL/CGAL",
        "demos": bool_demos,
    })

    # ── Mesh Repair ────────────────────────────────────────────────
    repair_demos = []

    # Create a mesh with isolated vertices
    box = make_box([0, 0, 0], [1, 1, 1])
    v = np.vstack([box.vertices, [[5, 5, 5], [6, 6, 6]]])  # add isolated verts
    f = box.faces
    dirty = pymesh.form_mesh(v, f)

    pv_dirty = pv_from_pymesh(dirty)
    render_mesh(pv_dirty,
                os.path.join(OUT_DIR, "repair_iso_before.png"),
                f"Input: {dirty.num_vertices} verts ({dirty.num_vertices - box.num_vertices} isolated)")

    t0 = time.perf_counter()
    clean, info = pymesh.remove_isolated_vertices(dirty)
    elapsed = time.perf_counter() - t0

    pv_clean = pv_from_pymesh(clean)
    render_mesh(pv_clean,
                os.path.join(OUT_DIR, "repair_iso_after.png"),
                f"Cleaned: {clean.num_vertices} verts  ({elapsed:.3f}s)",
                color=MESH_COLOR_OUT)

    repair_demos.append({
        "name": "repair_iso",
        "verts_in": dirty.num_vertices,
        "faces_in": dirty.num_faces,
        "verts_out": clean.num_vertices,
        "faces_out": clean.num_faces,
        "elapsed": elapsed,
        "code": textwrap.dedent("""\
            import pymesh

            # mesh has extra isolated vertices
            clean, info = pymesh.remove_isolated_vertices(mesh)
            print(f"Removed {info['num_vertex_removed']} vertices")"""),
        "after_label": "Cleaned",
    })

    # Remove duplicated faces
    box2 = make_box([0, 0, 0], [1, 1, 1])
    v2 = box2.vertices
    f2 = np.vstack([box2.faces, box2.faces[:4]])  # duplicate first 4 faces
    dirty2 = pymesh.form_mesh(v2, f2)

    pv_dirty2 = pv_from_pymesh(dirty2)
    render_mesh(pv_dirty2,
                os.path.join(OUT_DIR, "repair_dup_before.png"),
                f"Input: {dirty2.num_faces} faces (4 duplicated)")

    t0 = time.perf_counter()
    clean2, info2 = pymesh.remove_duplicated_faces(dirty2)
    elapsed2 = time.perf_counter() - t0

    pv_clean2 = pv_from_pymesh(clean2)
    render_mesh(pv_clean2,
                os.path.join(OUT_DIR, "repair_dup_after.png"),
                f"Cleaned: {clean2.num_faces} faces  ({elapsed2:.3f}s)",
                color=MESH_COLOR_OUT)

    repair_demos.append({
        "name": "repair_dup",
        "verts_in": dirty2.num_vertices,
        "faces_in": dirty2.num_faces,
        "verts_out": clean2.num_vertices,
        "faces_out": clean2.num_faces,
        "elapsed": elapsed2,
        "code": textwrap.dedent("""\
            import pymesh

            # mesh has duplicated faces
            clean, info = pymesh.remove_duplicated_faces(mesh)"""),
        "after_label": "Cleaned",
    })

    sections.append({
        "title": "Mesh Repair",
        "subtitle": "Remove isolated vertices, duplicated faces, degenerate triangles",
        "demos": repair_demos,
    })

    # ── Remeshing ──────────────────────────────────────────────────
    remesh_demos = []

    sphere = pymesh.generate_icosphere(1.0, [0, 0, 0], refinement_order=2)

    pv_sphere = pv_from_pymesh(sphere)
    render_mesh(pv_sphere,
                os.path.join(OUT_DIR, "remesh_before.png"),
                f"Input: {sphere.num_vertices} verts, {sphere.num_faces} faces")

    t0 = time.perf_counter()
    refined, _ = pymesh.split_long_edges(sphere, 0.2)
    elapsed = time.perf_counter() - t0

    pv_refined = pv_from_pymesh(refined)
    render_mesh(pv_refined,
                os.path.join(OUT_DIR, "remesh_after.png"),
                f"Refined: {refined.num_vertices} verts, {refined.num_faces} faces  ({elapsed:.2f}s)",
                color=MESH_COLOR_OUT)

    remesh_demos.append({
        "name": "remesh",
        "verts_in": sphere.num_vertices,
        "faces_in": sphere.num_faces,
        "verts_out": refined.num_vertices,
        "faces_out": refined.num_faces,
        "elapsed": elapsed,
        "code": textwrap.dedent("""\
            import pymesh

            sphere = pymesh.generate_icosphere(
                1.0, [0, 0, 0],
                refinement_order=2)

            refined, _ = pymesh.split_long_edges(
                sphere, 0.2)"""),
        "after_label": "Refined",
    })

    sections.append({
        "title": "Remeshing",
        "subtitle": "Edge splitting, collapse, and adaptive refinement",
        "demos": remesh_demos,
    })

    # ── Convex Hull ────────────────────────────────────────────────
    hull_demos = []

    box3 = make_box([0, 0, 0], [1, 1, 1])

    pv_box3 = pv_from_pymesh(box3)
    render_mesh(pv_box3,
                os.path.join(OUT_DIR, "hull_before.png"),
                f"Input: {box3.num_vertices} verts, {box3.num_faces} faces")

    t0 = time.perf_counter()
    hull = pymesh.convex_hull(box3)
    elapsed = time.perf_counter() - t0

    pv_hull = pv_from_pymesh(hull)
    render_mesh(pv_hull,
                os.path.join(OUT_DIR, "hull_after.png"),
                f"Convex Hull: {hull.num_vertices} verts, {hull.num_faces} faces  ({elapsed:.3f}s)",
                color=MESH_COLOR_OUT)

    hull_demos.append({
        "name": "hull",
        "verts_in": box3.num_vertices,
        "faces_in": box3.num_faces,
        "verts_out": hull.num_vertices,
        "faces_out": hull.num_faces,
        "elapsed": elapsed,
        "code": textwrap.dedent("""\
            import pymesh

            mesh = pymesh.generate_box_mesh(
                np.array([0, 0, 0]),
                np.array([1, 1, 1]))

            hull = pymesh.convex_hull(mesh)"""),
        "after_label": "Convex Hull",
    })

    sections.append({
        "title": "Convex Hull",
        "subtitle": "Compute the convex hull of a mesh",
        "demos": hull_demos,
    })

    # ── Generate HTML ──────────────────────────────────────────────
    generate_html(sections)
    print(f"Demo site generated in {OUT_DIR}/")


if __name__ == "__main__":
    main()
