#!/usr/bin/env python3
"""Debug mesh creation issue"""

import os
import sys
from pathlib import Path
import io
import trimesh

# Add the src directory to the path
sys.path.append(str(Path(__file__).parent / "src"))

def debug_mesh_creation():
    """Debug why mesh_from_memory is creating empty meshes"""
    
    print("🔍 DEBUG: Testing mesh creation with OBJ file data...")
    
    # Test with a known good OBJ file first
    obj_file = "static/sessions/frames/frame_0000.obj"
    
    if not os.path.exists(obj_file):
        print(f"❌ Test OBJ file not found: {obj_file}")
        return False
    
    # Load the OBJ file directly with trimesh to see if it works
    print(f"📋 Testing direct OBJ loading: {obj_file}")
    
    try:
        mesh_direct = trimesh.load(obj_file, force='mesh')
        print(f"✅ Direct load: {len(mesh_direct.vertices)} vertices, {len(mesh_direct.faces)} faces")
        print(f"   Bounds: {mesh_direct.bounds}")
        print(f"   Is empty: {mesh_direct.is_empty}")
    except Exception as e:
        print(f"❌ Direct load failed: {e}")
        return False
    
    # Now test our mesh_from_memory function
    print(f"\n📋 Testing mesh_from_memory with same data...")
    
    try:
        # Read OBJ file content
        with open(obj_file, 'r') as f:
            obj_content = f.read()
        
        print(f"📄 OBJ file size: {len(obj_content)} characters")
        
        # Parse vertices and faces manually
        lines = obj_content.strip().split('\n')
        vertices = []
        faces = []
        
        for line in lines:
            if line.startswith('v '):
                parts = line.split()
                if len(parts) >= 4:
                    vertex = [float(parts[1]), float(parts[2]), float(parts[3])]
                    vertices.append(vertex)
            elif line.startswith('f '):
                parts = line.split()
                if len(parts) >= 4:
                    # Convert to 0-based indices
                    face = [int(parts[i]) - 1 for i in range(1, len(parts))]
                    faces.append(face)
        
        print(f"📊 Parsed: {len(vertices)} vertices, {len(faces)} faces")
        
        # Test our mesh_from_memory function
        def mesh_from_memory_debug(vertices, faces):
            """Debug version of mesh_from_memory"""
            if not vertices or not faces:
                print(f"ERROR: mesh_from_memory - empty data: vertices={len(vertices)}, faces={len(faces)}")
                return None
                
            print(f"DEBUG: Creating mesh from {len(vertices)} vertices, {len(faces)} faces")
            
            lines = []
            for v in vertices:
                lines.append(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}")
            for face in faces:
                if len(face) >= 3:  # Ensure valid face
                    lines.append("f " + " ".join(str(i+1) for i in face))
                else:
                    print(f"WARNING: Skipping invalid face with {len(face)} vertices: {face}")
            
            obj_data = "\n".join(lines)
            print(f"DEBUG: Generated OBJ data: {len(obj_data)} characters, {len(lines)} lines")
            
            # Show first few lines
            sample_lines = obj_data.split('\n')[:10]
            print(f"DEBUG: Sample OBJ lines:")
            for i, line in enumerate(sample_lines):
                print(f"   {i+1}: {line}")
            
            obj_file = io.StringIO(obj_data)
            
            try:
                mesh = trimesh.load(obj_file, file_type='obj')
                if mesh is None:
                    print("ERROR: trimesh.load returned None")
                    return None
                if hasattr(mesh, 'is_empty') and mesh.is_empty:
                    print("ERROR: Created mesh is empty")
                    return None
                print(f"DEBUG: Successfully created mesh with {len(mesh.vertices)} vertices, {len(mesh.faces)} faces")
                print(f"DEBUG: Mesh bounds: {mesh.bounds}")
                return mesh
            except Exception as e:
                print(f"ERROR: Failed to create mesh: {e}")
                import traceback
                traceback.print_exc()
                return None
        
        mesh_from_mem = mesh_from_memory_debug(vertices, faces)
        
        if mesh_from_mem is not None:
            print(f"✅ mesh_from_memory SUCCESS!")
            print(f"   Vertices: {len(mesh_from_mem.vertices)}")
            print(f"   Faces: {len(mesh_from_mem.faces)}")
            print(f"   Bounds: {mesh_from_mem.bounds}")
        else:
            print(f"❌ mesh_from_memory FAILED!")
            
            # Try debugging with a simple cube
            print(f"\n🧪 Testing with simple cube...")
            cube_vertices = [
                [0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0],  # bottom
                [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]   # top
            ]
            cube_faces = [
                [0, 1, 2, 3],  # bottom
                [4, 7, 6, 5],  # top
                [0, 4, 5, 1],  # front
                [2, 6, 7, 3],  # back
                [0, 3, 7, 4],  # left
                [1, 5, 6, 2]   # right
            ]
            
            cube_mesh = mesh_from_memory_debug(cube_vertices, cube_faces)
            if cube_mesh is not None:
                print(f"✅ Simple cube worked - issue is with complex geometry")
            else:
                print(f"❌ Even simple cube failed - issue is in mesh_from_memory function")
        
        return True
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    debug_mesh_creation() 