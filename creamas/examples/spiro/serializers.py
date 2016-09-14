'''
Testing serializer.
'''
import pickle

from spiro_agent_mp import SpiroArtifact

def get_spiro_ser():
    return SpiroArtifact, pickle.dumps, pickle.loads
