
import face_recognition
from pathlib import Path
import numpy as np
import re

DATA = Path('./Database/')
ENCODINGS = Path('./Weights/FaceRec_Encs/')
class FaceRecModel:
    def __init__(self,enc_model_size='large',frame_resz=0.2,upsample=1,model='hog',num_jitters=1,thres=0.4,enc_force_load=False):
        self.enc_model_size= enc_model_size
        self.frame_resz=frame_resz
        
        # How many times to upsample the image looking for faces. 
        # Higher numbers find smaller faces.
        self.upsample=upsample

        # “hog” is less accurate but faster on CPUs. 
        # “cnn” is a more accurate deep-learning model 
        # which is GPU/CUDA accelerated (if available)
        self.model=model

        # How many times to re-sample the face when calculating encoding. 
        # Higher is more accurate, but slower
        self.num_jitters = num_jitters

        self.thres = thres
        self.enc_force_load=enc_force_load

    def preprocess(self,enc_list=[]):
        '''
        Load data and/or pretrained model
        '''
        self.face_encs,self.face_names=[],[]

        # empty database
        if self.enc_force_load or len(list(ENCODINGS.glob('**/*.npy')))==0:
            # remove all encodings
            print(f'Deleting all encodings in {ENCODINGS}')
            for f in ENCODINGS.glob('**/*.npy'):
                try: f.unlink()
                except OSError as e:
                    print(f'Error deleting {f}: {e}')

            files = [p for p in DATA.glob('**/*') if p.suffix in {'.png','.jpg','.jpeg'}]
            for f in files:
                print(f'Getting encodings from {f}...')
                img = face_recognition.load_image_file(f)
                enc = self.get_encodings(img)[0]
                name = Path(f).stem.lower()

                # write to encoding directory
                np.save(ENCODINGS/f'{name}.npy',enc)
                self.face_encs.append(enc)
                self.face_names.append(name)   

        else:
            for f in ENCODINGS.glob('**/*.npy'):
                print(f'Loading encodings from {f}...')
                name = Path(f).stem.lower()
                enc = np.load(ENCODINGS/f'{name}.npy')
                self.face_encs.append(enc)
                self.face_names.append(name)
            # Get encodings from extra list
            for name in enc_list.split():
                name = name.strip().lower()
                print(f'Get extra encodings for {name}...')
                f = [p for p in DATA.glob(f'**/{name}.*') if p.suffix in {'.png','.jpg','.jpeg'}]
                if len(f)==0 or len(f)>1:
                    print(f'Error getting encodings for {name}: too many images or image not found')
                    continue
                img = face_recognition.load_image_file(f[0])
                enc = self.get_encodings(img)[0]
                # write to encoding directory
                np.save(ENCODINGS/f'{name}.npy',enc)
                self.face_encs.append(enc)
                self.face_names.append(name) 

    def get_locations(self,frame):
        '''
        Return locations of faces from 1 single frame
        
        '''
        return face_recognition.face_locations(frame,number_of_times_to_upsample=self.upsample,model=self.model)
    
    def get_encodings(self,frame,locations=None):
        '''
        Return face encodings given frame and locations
        '''
        return face_recognition.face_encodings(frame,locations,model=self.enc_model_size,num_jitters = self.num_jitters)

    def predict(self,frame):
        '''
        Lower threshold => stricter to get a face in encoding database
        '''
        frame = frame[:,:,::-1] # to rgb
        current_locations = self.get_locations(frame)
        current_encodings = self.get_encodings(frame,current_locations)

        current_names = []
        name="Unknown"
        for enc in current_encodings:
            face_distances = face_recognition.face_distance(self.face_encs, enc)
            best_match_index = np.argmin(face_distances)
            if face_distances[best_match_index]<=self.thres:
                name = self.face_names[best_match_index]

            current_names.append(name)

        return current_locations,current_names



    

