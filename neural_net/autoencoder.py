from keras.layers import Input, Dense
from keras.models import Model

board_size = 64

board_input = Input(shape=(board_size,))

encoded = Dense(32, activation='relu')(board_input)

decoded = Dense(64, activation='sigmoid')(encoded)

# The autoencoder is the full model that feeds back to itself
autoencoder = Model(board_input, decoded)

# The encoder is the encoding part alone
encoder = Model(input, encoded)

# The decoder is the decoder part alone
encoded_input = Input(shape=(board_size,))
decoded_layer = autoencoder.layers[-1]
decoder = Model(encoded_input, decoded_layer(encoded_input))
