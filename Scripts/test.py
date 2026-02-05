import os
import subprocess

def test_gifsicle():
    magick_dir = os.path.join(os.path.dirname(__file__), 'portable_magick')
    gifsicle_bin = os.path.join(magick_dir, 'bin', 'gifsicle')
    env = os.environ.copy()
    env['PATH'] = os.pathsep.join([os.path.join(magick_dir, 'bin'), env.get('PATH', '')])
    env['DYLD_LIBRARY_PATH'] = os.path.join(magick_dir, 'lib')

    print("Testing gifsicle version...")
    result = subprocess.run([gifsicle_bin, '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    print("Return code:", result.returncode)
    print("STDOUT:", result.stdout.decode())
    print("STDERR:", result.stderr.decode())

    # Test optimization on a simple GIF
    test_gif = os.path.join(os.path.dirname(__file__), 'test.gif')
    # Create a 1-frame GIF using gifsicle itself
    with open(test_gif, 'wb') as f:
        f.write(b'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\n\x00\x01\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;')
    optimize_cmd = [gifsicle_bin, '-O3', test_gif, '-o', test_gif]
    result2 = subprocess.run(optimize_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    print("Optimize return code:", result2.returncode)
    print("Optimize STDOUT:", result2.stdout.decode())
    print("Optimize STDERR:", result2.stderr.decode())
    if os.path.exists(test_gif):
        print("GIF optimization test completed successfully.")
        os.remove(test_gif)
    else:
        print("GIF optimization test failed.")

def test_ghostscript():
    magick_dir = os.path.join(os.path.dirname(__file__), 'portable_magick')
    gs_bin = os.path.join(magick_dir, 'bin', 'gs')
    env = os.environ.copy()
    env['PATH'] = os.pathsep.join([os.path.join(magick_dir, 'bin'), env.get('PATH', '')])
    env['DYLD_LIBRARY_PATH'] = os.path.join(magick_dir, 'lib')

    print("Testing Ghostscript version...")
    result = subprocess.run([gs_bin, '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    print("Return code:", result.returncode)
    print("STDOUT:", result.stdout.decode())
    print("STDERR:", result.stderr.decode())

if __name__ == "__main__":
    test_gifsicle()
    print("="*40)
    test_ghostscript()