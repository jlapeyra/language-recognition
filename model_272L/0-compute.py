from language_model import *
NUM_ALPHABET_CHARS = 38
NUM_ALPHABET_BLOCKS = 2

metamodel = MetaLanguageModel()
metamodel.train('training_272L', folder_save='model_272L')

# time = 129.49922227859497
# time/lang = 0.4761