from keras.layers import Input, Dense
from keras.models import Model
import numpy as np

from game.reversi import Reversi

board_size = 64
encoded_size = 32

board_input = Input(shape=(board_size,))

encoded = Dense(encoded_size, activation='relu')(board_input)

decoded = Dense(board_size, activation='sigmoid')(encoded)

# The autoencoder is the full model that feeds back to itself
autoencoder = Model(board_input, decoded)

# The encoder is the encoding part alone
encoder = Model(board_input, encoded)

# The decoder is the decoder part alone
encoded_input = Input(shape=(encoded_size,))
decoder_layer = autoencoder.layers[-1]
decoder = Model(encoded_input, decoder_layer(encoded_input))

autoencoder.compile(optimizer='adadelta', loss='binary_crossentropy')

amount_games = 5000
epochs = 500
batch_size = 1000

train = []
for i in range(amount_games):
    print('playing train game {}'.format(i))
    r = Reversi(silent=True)
    (_, _, _, boards) = r.play_game()
    numpy_boards = [np.asarray(b).reshape(board_size) for b in boards]
    train.extend(numpy_boards)

test = []
for i in range(amount_games):
    print('playing test game {}'.format(i))
    r = Reversi(silent=True)
    (_, _, _, boards) = r.play_game()
    numpy_boards = [np.asarray(b).reshape(board_size) for b in boards]
    test.extend(numpy_boards)


train_np = np.asarray(train)
test_np = np.asarray(test)

autoencoder.fit(train_np, train_np,
                epochs=epochs,
                batch_size=batch_size,
                shuffle=True,
                validation_data=(test_np, test_np))

input_board = test_np[30]
encoded_board = encoder.predict(np.reshape(input_board, (1, 64)))
decoded_board = decoder.predict(encoded_board)

print(str(input_board.reshape((8, 8))))
print(str(encoded_board))
print(str(decoded_board.reshape((1, 8, 8))))

autoencoder.save('reversiencodermodel.h5')
