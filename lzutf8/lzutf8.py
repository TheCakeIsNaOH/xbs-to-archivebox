"""
Pure Python Implementation of the TypeScript library "LZ-UTF8" originally
written by Rotem Dan.

Python Code   -> Copyright (c) 2019 b-01
Original Code -> Copyright (c) 2014-2018, Rotem Dan <rotemdan@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import abc


def rshift(val, n):
    """
    Python equivalent to TypeScripts >>> operator.

    @see https://stackoverflow.com/questions/5832982/how-to-get-the-logical-right-binary-shift-in-python
    """
    return (val % 0x100000000) >> n


class CompressorHashTable(metaclass=abc.ABCMeta):
    """
    @see: https://github.com/rotemdan/lzutf8.js/blob/a651a467a3456ecac302afb4ea9e320731f182f6/src/Compression/CompressorHashTable.ts#L1
    """

    @abc.abstractmethod
    def addValueToBucket(self, bucketIndex, valueToAdd):
        pass

    @abc.abstractmethod
    def getArraySegmentForBucketIndex(self, bucketIndex, outputObject=None):
        pass

    @abc.abstractmethod
    def getUsedBucketCount(self):
        pass

    @abc.abstractmethod
    def getTotalElementCount(self):
        pass


class CompressorSimpleHashTable(CompressorHashTable):
    """
    @see https://github.com/rotemdan/lzutf8.js/blob/a651a467a3456ecac302afb4ea9e320731f182f6/src/Compression/CompressorSimpleHashTable.ts#L1
    """

    def __init__(self):
        super().__init__()
        self._buckets = dict()

    def addValueToBucket(self, bucketIndex, valueToAdd):
        bucket = self._buckets.get(bucketIndex, None)
        if not bucket:
            self._buckets[bucketIndex] = [valueToAdd]
        else:
            bucket.append(valueToAdd)

    def getArraySegmentForBucketIndex(self, bucketIndex, outputObject=None):
        bucket = self._buckets.get(bucketIndex, None)
        if not outputObject:
            outputObject = bucket
        return outputObject

    def getUsedBucketCount(self):
        return len(self._buckets)

    def getTotalElementCount(self):
        return sum(map(len, self._buckets.values()))


class Compressor:
    MinimumSequenceLength = 4
    MaximumSequenceLength = 31
    MaximumMatchDistance = 32767
    PrefixHashTableSize = 65537

    def __init__(self, customHashTable=None):
        self.inputBuffer = list()
        self.inputBufferStreamOffset = 1

        self.outputBuffer = None
        self.outputBufferPosition = 0

        self.prefixHashTable = None

        self.__reusableArraySegmentObject = None

        if customHashTable:
            self.prefixHashTable = customHashTable()
        else:
            self.prefixHashTable = CompressorSimpleHashTable()

    def _compressUtf8Block(self, utf8Bytes):
        if not utf8Bytes:
            return list()

        self.outputBuffer = list()
        self.outputBufferPosition = 0

        # const
        bufferStartingReadOffset = self._cropAndAddNewBytesToInputBuffer(utf8Bytes)
        # const
        inputBuffer = self.inputBuffer
        # const
        inputBufferLength = len(self.inputBuffer)

        latestMatchEndPosition = 0

        readPosition = bufferStartingReadOffset
        while readPosition < inputBufferLength:
            inputValue = inputBuffer[readPosition]
            withinAMatchedRange = readPosition < latestMatchEndPosition

            # Last 3 bytes are not matched
            if readPosition > (inputBufferLength - self.MinimumSequenceLength):
                if not withinAMatchedRange:
                    self._outputRawByte(inputValue)
                readPosition += 1
                continue

            # Find the target bucket index
            targetBucketIndex = self._getBucketIndexForPrefix(readPosition)

            if not withinAMatchedRange:
                # Try to find the longest match for the sequence starting at the current position
                matchLocator = self._findLongestMatch(readPosition, targetBucketIndex)

                # If match found
                if matchLocator:
                    # Output a pointer to the match
                    self._outputPointerBytes(matchLocator["length"], matchLocator["distance"])

                    # Keep the end position of the match
                    latestMatchEndPosition = readPosition + matchLocator["length"]
                    withinAMatchedRange = True

            # If not in a range of a match, output the literal byte
            if not withinAMatchedRange:
                self._outputRawByte(inputValue)

            # Add the current 4 byte sequence to the hash table
            # (note that input stream offset starts at 1, so it will never equal 0, thus the hash
            # table can safely use 0 as an empty bucket slot indicator - this property is critical for the custom hash table implementation).
            #
            # const
            inputStreamPosition = self.inputBufferStreamOffset + readPosition
            self.prefixHashTable.addValueToBucket(targetBucketIndex, inputStreamPosition)
            readPosition += 1
        return self.outputBuffer[0:self.outputBufferPosition]

    def _findLongestMatch(self, matchedSequencePosition, bucketIndex):
        # const
        bucket = self.prefixHashTable.getArraySegmentForBucketIndex(bucketIndex, self.__reusableArraySegmentObject)

        if not bucket:
            return None

        # const
        inputBuffer = self.inputBuffer

        longestMatchDistance = None
        longestMatchLength = 0

        for i in range(len(bucket)):
            # Adjust to the actual buffer position. Note: position might be negative (not in the current buffer)
            #
            # startPosition is always 0 as we are working on real data copies.
            # this.startPosition + this.length - 1 - reverseIndex
            bucket_index = len(bucket) - 1 - i
            # const
            testedSequencePosition = bucket[bucket_index] - self.inputBufferStreamOffset
            # const
            testedSequenceDistance = matchedSequencePosition - testedSequencePosition

            # Find the length to surpass for this match
            lengthToSurpass = 0

            if not longestMatchDistance:
                lengthToSurpass = self.MinimumSequenceLength - 1
            elif longestMatchDistance < 128 and testedSequenceDistance >= 128:
                lengthToSurpass = longestMatchLength + rshift(longestMatchLength, 1)  # floor(l * 1.5)
            else:
                lengthToSurpass = longestMatchLength

            # Break if any of the conditions occur
            if (testedSequenceDistance > self.MaximumMatchDistance or lengthToSurpass >= self.MaximumSequenceLength or
                    matchedSequencePosition + lengthToSurpass >= len(inputBuffer)):
                break

            # Quick check to see if there's any point comparing all the bytes.
            if inputBuffer[testedSequencePosition + lengthToSurpass] != inputBuffer[matchedSequencePosition +
                                                                                    lengthToSurpass]:
                continue

            offset = 0
            while True:
                if (matchedSequencePosition + offset == len(inputBuffer) or
                        inputBuffer[testedSequencePosition + offset] != inputBuffer[matchedSequencePosition + offset]):
                    if offset > lengthToSurpass:
                        longestMatchDistance = testedSequenceDistance
                        longestMatchLength = offset
                    break
                elif offset == self.MaximumSequenceLength:
                    return {"distance": testedSequenceDistance, "length": self.MaximumSequenceLength}
                offset += 1
        if longestMatchDistance:
            return {"distance": longestMatchDistance, "length": longestMatchLength}
        else:
            return None

    def _getBucketIndexForPrefix(self, startPosition):
        return (
                self.inputBuffer[startPosition] * 7880599 + 
                self.inputBuffer[startPosition + 1] * 39601 +
                self.inputBuffer[startPosition + 2] * 199 + 
                self.inputBuffer[startPosition + 3]
        ) % self.PrefixHashTableSize

    def _outputPointerBytes(self, length, distance):
        if distance < 128:
            self._outputRawByte(192 | length)
            self._outputRawByte(distance)
        else:
            self._outputRawByte(224 | length)
            self._outputRawByte(rshift(distance, 8))
            self._outputRawByte(distance & 255)

    def _outputRawByte(self, value):
        self.outputBuffer.insert(self.outputBufferPosition, value)
        self.outputBufferPosition += 1

    def _cropAndAddNewBytesToInputBuffer(self, newInput):
        if not self.inputBuffer:
            self.inputBuffer = newInput
            return 0
        else:
            # const
            cropLength = min(len(self.inputBuffer), self.MaximumMatchDistance)
            # const
            cropStartOffset = len(self.inputBuffer) - cropLength

            self.inputBuffer = self.inputBuffer[cropStartOffset:cropStartOffset + cropLength] + newInput
            self.inputBufferStreamOffset += cropStartOffset
            return cropLength

    def compressBlock(self, input_bytes):
        if not input_bytes:
            raise TypeError("compressBlock: NoneType received")

        try:
            input_bytes = input_bytes.encode("utf-8")
        except AttributeError:
            # already bytes
            pass
        return self._compressUtf8Block(input_bytes)

    def compressBlockToBytes(self, input_bytes):
        return bytes(self.compressBlock(input_bytes))

    def compressBlockToString(self, input_bytes):
        return self.compressBlockToBytes(input_bytes).decode("utf-8")


class Decompressor:
    """
    LZ-UTF8 Decompressor

    @see https://github.com/rotemdan/lzutf8.js/blob/a651a467a3456ecac302afb4ea9e320731f182f6/src/Decompression/Decompressor.ts#L2
    """
    MAXIMUMMATCHDISTANCE = 32767

    def __init__(self):
        self.outputBuffer = None
        self.outputPosition = 0

        self.inputBufferRemainder = None
        self.outputBufferRemainder = None

    def _outputByte(self, value):
        self.outputBuffer.append(value)
        self.outputPosition += 1

    def _cropOutputBufferToWindowAndInitialize(self, initialCapacity):
        if not self.outputBuffer:
            self.outputBuffer = []
            return 0

        cropLength = min(self.outputPosition, Decompressor.MAXIMUMMATCHDISTANCE)
        self.outputBuffer = self.outputBuffer[(self.outputPosition - cropLength):cropLength]

        self.outputPosition = cropLength

        if self.outputBufferRemainder:
            for i in range(len(self.outputBufferRemainder)):
                self._outputByte(self.outputBufferRemainder[i])
            self.outputBufferRemainder = None
        return cropLength

    def _rollBackIfOutputBufferEndsWithATruncatedMultibyteSequence(self):
        for offset in range(1, 5):
            if self.outputPosition - offset < 0:
                return
            value = self.outputBuffer[self.outputPosition - offset]
            if ((offset < 4 and rshift(value, 3) == 30) or  # Leading byte of a 4 byte UTF8 sequence
                (offset < 3 and rshift(value, 4) == 14) or  # Leading byte of a 3 byte UTF8 sequence
                (offset < 2 and rshift(value, 5) == 6)):  # Leading byte of a 2 byte UTF8 sequence

                self.outputBufferRemainder = self.outputBuffer[self.outputPosition - offset, self.outputPosition]
                self.outputPosition = self.outputPosition - offset
                return

    def decompressBlock(self, input_list):
        if self.inputBufferRemainder:
            input_list = self.inputBufferRemainder + input_list
            self.inputBufferRemainder = []

        outputStartPosition = self._cropOutputBufferToWindowAndInitialize(max(len(input_list) * 4, 1024))

        inputLength = len(input_list)
        readPosition = 0
        while readPosition < inputLength:
            inputValue = input_list[readPosition]
            if rshift(inputValue, 6) != 3:
                # If at the continuation byte of a UTF-8 codepoint sequence, output the literal value and continue
                self._outputByte(inputValue)
                # increment read position
                readPosition += 1
                continue
            # At this point it is known that the current byte is the lead byte of either a UTF-8 codepoint or a sized pointer sequence.
            sequenceLengthIdentifier = rshift(inputValue, 5)  # 6 for 2 bytes, 7 for at least 3 bytes
            # If bytes in read position imply the start of a truncated input sequence (either a literal codepoint or a pointer)
            # keep the remainder to be decoded with the next buffer
            if readPosition == (inputLength - 1) or (readPosition == (inputLength - 2) and
                                                     sequenceLengthIdentifier == 7):
                self.inputBufferRemainder = input_list[readPosition:]
                break
            # If at the leading byte of a UTF-8 codepoint byte sequence
            if rshift(input_list[readPosition + 1], 7) == 1:
                # Output the literal value
                self._outputByte(inputValue)
            else:
                # Beginning of a pointer sequence
                matchLength = inputValue & 31
                matchDistance = 0
                if sequenceLengthIdentifier == 6:  # 2 byte pointer type, distance was smaller than 128
                    matchDistance = input_list[readPosition + 1]
                    readPosition += 1
                else:  # 3 byte pointer type, distance was greater or equal to 128
                    matchDistance = (input_list[readPosition + 1] << 8) | (input_list[readPosition + 2])  # Big endian
                    readPosition += 2

                matchPosition = self.outputPosition - matchDistance
                # Copy the match bytes to output
                for offset in range(matchLength):
                    self._outputByte(self.outputBuffer[matchPosition + offset])
            # increment read position
            readPosition += 1
        self._rollBackIfOutputBufferEndsWithATruncatedMultibyteSequence()
        return self.outputBuffer[outputStartPosition:(
            outputStartPosition + (self.outputPosition - outputStartPosition))]

    def decompressBlockToString(self, input_list):
        return bytes(self.decompressBlock(input_list)).decode("utf-8")
