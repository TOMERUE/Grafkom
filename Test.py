from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import sys

# Variabel rotasi
rotate_x = 0
rotate_y = 0

# Variabel translasi
translate_x = 0.0
translate_y = 0.0
translate_z = -5.0

def init():
    glClearColor(0.1, 0.1, 0.1, 1.0)  # Warna latar belakang
    glEnable(GL_DEPTH_TEST)           # Aktifkan depth buffer

    # Aktifkan pencahayaan
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)

    # Komponen cahaya (Phong Model)
    ambient = [0.2, 0.2, 0.2, 1.0]
    diffuse = [0.7, 0.7, 0.7, 1.0]
    specular = [1.0, 1.0, 1.0, 1.0]
    position = [1.0, 1.0, 1.0, 0.0]

    glLightfv(GL_LIGHT0, GL_AMBIENT, ambient)
    glLightfv(GL_LIGHT0, GL_DIFFUSE, diffuse)
    glLightfv(GL_LIGHT0, GL_SPECULAR, specular)
    glLightfv(GL_LIGHT0, GL_POSITION, position)

    # Material objek
    glMaterialfv(GL_FRONT, GL_SPECULAR, specular)
    glMaterialf(GL_FRONT, GL_SHININESS, 50.0)


def draw_cube():
    glBegin(GL_QUADS)
    # Depan
    glNormal3f(0, 0, 1)
    glVertex3f(-1, -1, 1)
    glVertex3f(1, -1, 1)
    glVertex3f(1, 1, 1)
    glVertex3f(-1, 1, 1)

    # Belakang
    glNormal3f(0, 0, -1)
    glVertex3f(-1, -1, -1)
    glVertex3f(-1, 1, -1)
    glVertex3f(1, 1, -1)
    glVertex3f(1, -1, -1)

    # Kanan
    glNormal3f(1, 0, 0)
    glVertex3f(1, -1, -1)
    glVertex3f(1, 1, -1)
    glVertex3f(1, 1, 1)
    glVertex3f(1, -1, 1)

    # Kiri
    glNormal3f(-1, 0, 0)
    glVertex3f(-1, -1, -1)
    glVertex3f(-1, -1, 1)
    glVertex3f(-1, 1, 1)
    glVertex3f(-1, 1, -1)

    # Atas
    glNormal3f(0, 1, 0)
    glVertex3f(-1, 1, -1)
    glVertex3f(-1, 1, 1)
    glVertex3f(1, 1, 1)
    glVertex3f(1, 1, -1)

    # Bawah
    glNormal3f(0, -1, 0)
    glVertex3f(-1, -1, -1)
    glVertex3f(1, -1, -1)
    glVertex3f(1, -1, 1)
    glVertex3f(-1, -1, 1)
    glEnd()


def display():
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()

    # Kamera: gluLookAt
    gluLookAt(0, 0, 5,
              0, 0, 0,
              0, 1, 0)

    # Transformasi objek
    glTranslatef(translate_x, translate_y, translate_z)
    glRotatef(rotate_x, 1, 0, 0)
    glRotatef(rotate_y, 0, 1, 0)

    draw_cube()
    glutSwapBuffers()


def reshape(width, height):
    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45, width / float(height), 1, 50.0)
    glMatrixMode(GL_MODELVIEW)


def keyboard(key, x, y):
    global translate_x, translate_y, translate_z
    key = key.decode('utf-8')
    if key == 'w':
        translate_y += 0.1
    elif key == 's':
        translate_y -= 0.1
    elif key == 'a':
        translate_x -= 0.1
    elif key == 'd':
        translate_x += 0.1
    elif key == 'z':
        translate_z += 0.1
    elif key == 'x':
        translate_z -= 0.1
    glutPostRedisplay()


def special_input(key, x, y):
    global rotate_x, rotate_y
    if key == GLUT_KEY_UP:
        rotate_x -= 5
    elif key == GLUT_KEY_DOWN:
        rotate_x += 5
    elif key == GLUT_KEY_LEFT:
        rotate_y -= 5
    elif key == GLUT_KEY_RIGHT:
        rotate_y += 5
    glutPostRedisplay()


def main():
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(800, 600)
    glutCreateWindow(b"3D Object with Lighting and Camera - PyOpenGL")
    init()
    glutDisplayFunc(display)
    glutReshapeFunc(reshape)
    glutKeyboardFunc(keyboard)
    glutSpecialFunc(special_input)
    glutMainLoop()


if __name__ == '__main__':
    main()
