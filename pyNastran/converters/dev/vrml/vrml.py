import numpy as np
from pyNastran.converters.dev.vrml.vrml_pyparsing import remove_comments, get_vrml_format
from pyNastran.converters.dev.vrml.vrml_to_dict import todict


def read_vrml(vrml_filename: str, debug=False, log=None):
    model = VRML(debug=debug, log=log)
    dict_model = model.read_vrml(vrml_filename)
    nodes, quads, tris = _load_geometry(dict_model, log)
    return nodes, quads, tris

def vrml_to_nastran(vrml_filename: str, nastran_filename: str, debug=False, log=None):
    """
    Converts a vrml file into a Nastran BDF.  Doesn't consider:
     - non-faceted geometry (only quads/tris, no spheres)
     - transforms

    """
    from pyNastran.bdf.field_writer import print_card_8, print_card_16

    nodes, quads, tris = read_vrml(vrml_filename, debug=debug, log=log)
    with open(nastran_filename, 'w') as bdf_file:
        bdf_file.write('$ pyNastran: punch=True\n')
        cp = 0
        for i, xyz in enumerate(nodes):
            card = ['GRID', i + 1, cp, ] + xyz.tolist()
            bdf_file.write(print_card_16(card))

        pid = 1
        ntris = len(tris)
        nquads = len(quads)
        if ntris:
            for ie, n123 in enumerate(tris + 1):
                card = ['CTRIA3', ie + 1, pid, ] + n123.tolist()
                bdf_file.write(print_card_8(card))
        if nquads:
            for ie, n1234 in enumerate(quads + 1):
                card = ['CQUAD4', ntris + ie + 1, pid, ] + n1234.tolist()
                bdf_file.write(print_card_8(card))

class VRML:
    def __init__(self, debug=False, log=None):
        self.debug = debug
        self.log = log

    def read_vrml(self, vrml_filename: str):
        with open(vrml_filename, 'r') as f:
            lines = f.readlines()

        vrml_format = get_vrml_format()

        lines = remove_comments(lines)
        txt = '\n'.join(lines)
        model = vrml_format.parseString(txt, parseAll=True)

        dict_model = todict(model)
        return dict_model


def stack(points):
    """stacks an array efficiently"""
    npoints = len(points)
    if npoints == 0:
        return []
    elif npoints == 1:
        return points[0]
    else:
        points = np.vstack(points)
    return points

def _load_geometry(dict_model, log):
    """converts a VRML dictionary into a faceted mesh"""
    all_points = []
    all_quads = []
    all_tris = []
    inode0 = 0
    for key, value in dict_model.items():
        if key in ['WorldInfo', 'NavigationInfo', 'Background']:
            continue
        elif key == 'Shape':
            shape = value
            for keyi, valuei in shape.items():
                if keyi in ['appearance']:
                    continue
                elif keyi == 'geometry':
                    if valuei == 'sphere':
                        unused_radius = 1.0
                    else:
                        raise NotImplementedError(f'keyi={keyi} valuei={valuei}')
                else:
                    raise NotImplementedError(f'keyi={keyi} valuei={valuei}')
            continue
        elif key == 'transforms':
            transforms = value
            for transform in transforms:
                #print('  t=', transform)
                for child in transform:
                    for keyi, valuei in child.items():
                        if keyi == 'appearance':
                            continue
                        elif keyi == 'indexed_face_set':
                            points, quads, tris = get_indexed_face_set(valuei)
                            all_points.append(points)
                            if len(quads):
                                all_quads.append(quads + inode0)
                            if len(tris):
                                all_tris.append(tris + inode0)
                            inode0 += points.shape[0]
                        else:
                            raise NotImplementedError(f'keyi={keyi} valuei={valuei}')
                            #print('    ', keyi, valuei)
        else:
            log.debug(f'key={key} value={value}')

    #print(all_points, len(all_points))
    all_points = stack(all_points)
    all_quads = stack(all_quads)
    all_tris = stack(all_tris)
    return all_points, all_quads, all_tris

def get_indexed_face_set(indexed_face_set):
    #print('    ', indexed_face_set)
    points = None
    quads = []
    tris = []
    for key, value in indexed_face_set.items():
        if key == 'coord':
            coord = value
            #print('      coord:', value)
            for keyi, valuei in coord.items():
                if keyi == 'point':
                    assert points is None
                    points = valuei
                else:
                    raise NotImplementedError(f'keyi={keyi} valuei={valuei}')
        elif key == 'quads':
            #print('      quads:', value)
            quads = value
        elif key == 'tris':
            #print('      tris:', value)
            tris = value
        elif key in ['crease_angle', 'tex_coord', 'normals']:
            continue
        else:
            raise NotImplementedError(key)
            #print('      ', key, value)
    return points, quads, tris

def spherified_cube(faces):
    """
    https://medium.com/game-dev-daily/four-ways-to-create-a-mesh-for-a-sphere-d7956b825db4
    """
    for f in faces:
        origin = get_origin(f)
        right = get_right_dir(f)
        up = get_up_dir(f)
        for j in div_count:
            for i in div_count:
                p = origin + 2.0 * (right * i + up * j) / div_count
                p2 = p * p
                rx = sqrt(1.0 - 0.5 * (p2.y + p2.z) + p2.y*p2.z/3.0)
                ry = sqrt(1.0 - 0.5 * (p2.z + p2.x) + p2.z*p2.x/3.0)
                rz = sqrt(1.0 - 0.5 * (p2.x + p2.y) + p2.x*p2.y/3.0)
                return (rx, ry, rz)
#model = Vrml_io()
#model.load_vrml_geometry(vrml_filename)

if 0:
    print('reading vrml file')
    ##txt = read_vrml('gbu.wrl')

    vrml_filename = 'gbu.wrl'
    #vrml_filename = 'pyramid_sphere.wrl'
    #txt = read_vrml(vrml_filename)
    #model = vrml_format.parseString(txt)
    _load_geometry(vrml_filename)
    #print(model)

    #dict_model = todict(model)
    # print(dict_model)
    #aaa
