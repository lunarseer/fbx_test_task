import argparse
import logging
from os import path, makedirs, listdir, remove
import shutil

import sys
import requests
from zipfile import ZipFile
import re

RUNDIRECTORY = path.dirname(__file__)
TEMPDIRECTORY = path.join(RUNDIRECTORY, 'temp_downloads')

formatter = logging.Formatter("%(name)s - %(asctime)s - [%(levelname)s] - %(message)s")
log = logging.getLogger('APP')
log.setLevel(logging.INFO)
fileHandler = logging.FileHandler("{0}/{1}.log".format(RUNDIRECTORY, 'processing'))
fileHandler.setFormatter(formatter)
consolehandler = logging.StreamHandler()
consolehandler.setFormatter(formatter)
log.addHandler(consolehandler)
log.addHandler(fileHandler)


import bpy


class Job:

    def __init__(self, *args, **kwargs):

        self.stages = [self.download,
                       self.extract_zip,
                       self.init_project,
                       self.import_fbx,
                       self.apply_transforms,
                       self.get_fbx_materials,
                       self.linktextures,
                       self.export_fbx,
                       self.copy_textures,
                       self.cleanup_downloads,
                       ]
        self.url = kwargs.get('url')
        self.output = kwargs.get('output')
        self.error = None
        self.archive = ''
        self.extract_path = ''
        self.tempassetpath = ''
        self.extractedfiles = []
        self.materials = []
        self.textures = []
        self.archivename = path.basename(self.url)
        self.assetname = path.splitext(self.archivename)[0]
        self.outputdir = path.join(self.output, self.assetname)

    def __repr__(self):
        return f'Asset {self.archivename}'

    def do(self):
        log.info(f'{self}: Start Processing...')
        while not any([self.error, not self.stages]):
            stage = self.stages.pop(0)
            stage()
        if self.error:
            log.error(f'{self}: Processing Failed')
            self.cleanup_downloads()
        else:
            log.info(f'{self}: Processing Completed')

    def init_project(self):
        bpy.ops.wm.read_homefile(app_template="")
        data = bpy.data.objects
        [data.remove(x, do_unlink=True) for x in bpy.context.scene.objects]  

    def cleanup_downloads(self):
        if path.exists(self.archive):
            remove(self.archive)
        if path.exists(self.extract_path):
            shutil.rmtree(self.extract_path)
        log.info(f'{self}: Downloads Deleted')

    def copy_textures(self):
        if self.textures:
            for tex in self.textures:
                shutil.copy2(tex, path.join(self.outputdir, path.basename(tex)))
            log.info(f'{self}: Textures copied to output dir')

    def export_fbx(self):
        if path.exists(self.outputdir):
            for f in listdir(self.outputdir):
                remove(path.join(self.outputdir, f))
            log.debug(f'{self}: output dir cleared')
        else:
            makedirs(self.outputdir)
            log.debug(f'{self}: output dir created')
        fbxfilepath = path.join(self.outputdir, f'{self.assetname}.fbx')
        bpy.ops.export_scene.fbx(filepath=fbxfilepath)
        log.info(f'{self}: FBX exported to output dir')

    def linktextures(self):
        imageextpat = re.compile(".*.jpg$|.*.png$")

        def is_valid(mat, tex):
            matnamepat = re.compile(f".*T_{self.assetname}_{mat.name}_(BC|N|O).*")
            if all([imageextpat.match(tex), matnamepat.match(tex)]):
                return True

        def attach_texture(mat, tex):
            mat.use_nodes = True
            shader_node = mat.node_tree.nodes.get('Principled BSDF')
            texchannel = path.splitext(path.basename(tex))[0].split('_')[-1]
            if texchannel == 'BC':
                texture_input = shader_node.inputs[0]
                texture = mat.node_tree.nodes.new('ShaderNodeTexImage')
                texture.image = bpy.data.images.load(tex)
                mat.node_tree.links.new(texture_input, texture.outputs['Color'])
            if texchannel == 'N':
                links = shader_node.inputs.get('Normal').links[0]
                texture_input = links.from_node.inputs.get('Color')
                texture = mat.node_tree.nodes.new('ShaderNodeTexImage')
                texture.image = bpy.data.images.load(tex)
                mat.node_tree.links.new(texture_input, texture.outputs['Color'])
            if texchannel == 'O':
                # I really dunno which channel is Opacity in Blender's Principled BSDF
                pass

        if self.materials:
            for mat in self.materials:
                textures = [x for x in self.extractedfiles if is_valid(mat, x)]
                for tex in textures:
                    attach_texture(mat, tex)
                self.textures += textures
            log.info(f'{self}: {len(self.textures)} Textures applied')
        else:
            log.debug(f'{self}: No Textures applied')

    def get_fbx_materials(self):
        materials = []
        for mesh in self.get_scene_meshes():
            material = mesh.active_material
            if material:
                materials.append(material)
        self.materials = materials
        
    def apply_transforms(self):
        for mesh in self.get_scene_meshes():
            geometry = bpy.data.objects.get(mesh.name, None)
            geometry.select_set(True)
            bpy.context.view_layer.objects.active = geometry
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            log.info(f'{self}: Mesh {mesh.name}: transforms applied')

    def import_fbx(self):
        for filepath in self.extractedfiles:
            if re.search('.*.fbx$', filepath):
                try:
                    bpy.ops.import_scene.fbx(filepath=filepath)
                    log.info(f'{self}: FBX imported')
                except:
                    log.warning(f'{self}: Cannot import {filepath}')
                    self.error = True

    def download(self):
        filename = self.url.split('/')[-1]
        filepath = path.join(TEMPDIRECTORY, filename)

        if path.exists(filepath):
            remove(filepath)
            log.debug(f'{self}: archive file overwrited')
        try:
            r = requests.get(self.url, allow_redirects=True, timeout=1)
            if r.status_code == 200:
                open(filepath, 'wb').write(r.content)
                log.info(f'{self}: archive downloaded')
                self.archive = filepath
            elif r.status_code == 404:
                self.error = True
                log.warning(f'{self}: URL is broken')
        except requests.exceptions.ConnectTimeout as e:
            log.warning(f'{self}: URL not accessible!')
            self.error = True

    def extract_zip(self):
        with ZipFile(self.archive, 'r') as file:
            self.extract_path = path.join(TEMPDIRECTORY, self.assetname)
            root_folder = path.commonprefix(file.namelist())
            if not path.exists(self.extract_path):
                makedirs(self.extract_path)
                log.debug(f'{self}: extraction path created')
            file.extractall(self.extract_path)
            log.info(f'{self}: archive extracted')
            result = self.extract_path
            if root_folder: #for case when files in subdirectory
                result = path.join(self.extract_path, root_folder)
            self.tempassetpath = result
            self.extractedfiles = [path.join(self.tempassetpath, x) for x in listdir(self.tempassetpath)]

    def get_scene_meshes(self):
        return [x for x in bpy.context.scene.objects if x.type == 'MESH']


class JobExecutor:
    jobs = []

    def __init__(self, *args):
        parser = argparse.ArgumentParser(description='simple parser')
        parser.add_argument('--file', dest="file", help='path to file with urls', required=True)
        parser.add_argument('--out', dest="output", help='path to output', required=True)
        parsed = parser.parse_args(*args)
        self.urlfile = parsed.file
        self.output = parsed.output

    def run(self):
        if not path.exists(TEMPDIRECTORY):
            makedirs(TEMPDIRECTORY)
            log.debug(f'{TEMPDIRECTORY} created')

        urls = self.__get_url_list()
        for url in urls:
            j = Job(url=url, output=self.output)
            j.do()
            self.jobs.append(j)
        log.info("{jc} URLs Processed - {er} Errors".format(
                                                     jc=len(self.jobs),
                                                     er=len([x for x in self.jobs if x.error])
                                                     ))

    def __get_url_list(self):
        if not all([path.exists(self.urlfile), path.isfile(self.urlfile)]):
            raise FileNotFoundError(f'{self.urlfile} Not Exists')
        else:
            with open(self.urlfile) as urlfile:
                urlist = [l.rstrip() for l in urlfile.readlines()]
                return urlist


if __name__ == '__main__':
    log.info(f'Starting in {RUNDIRECTORY}')
    argv = sys.argv[sys.argv.index('--') + 1:]
    executor = JobExecutor(argv)
    executor.run()
