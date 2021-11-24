from ALPSOccupancyGrid_pb2 import ALPSOccupancyGrid
from PIL import Image
import argparse
import numpy as np
import lzma
import sys
import os


def process_image(im):
    # Remove first channel from image
    single_channel = im.getchannel(0)
    
    # Use numpy to normalize cell data and serialize to bytes
    npdata = np.asarray(single_channel, dtype=np.uint32)
    npdata = np.where(npdata <= 127, 0, 0xFFFFFFFF)
    npdata = npdata.astype('uint32')
    #print(npdata)
    print(npdata.shape)
    return npdata.tobytes()

###### Deserializing functions ######
def read_compressed_bytes(file_path):
    # read compressed bytes file and return decompressed data
    file = lzma.LZMAFile(file_path, mode="rb")
    data = file.read()
    return data

def deserialize_protobuf_obj(serialized_data):
    # deserialize data back to a protobuf OccupancyGrid object
    occupancy_grid_obj = OccupancyGrid()
    occupancy_grid_obj.ParseFromString(serialized_data)
    return occupancy_grid_obj

def deserialize_occupancy_grid_image(occupancy_grid_obj):
    # deserialize occupancy_grid_obj grid back to an image
    nparray = np.frombuffer(occupancy_grid_obj.grid, dtype = np.uint32)
    nparray = nparray.reshape(occupancy_grid_obj.height, occupancy_grid_obj.width)
    return nparray
    


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Occupancy Grid Converter')
    parser.add_argument('-i', '--image_path', required=True, help='Absolute path to image')
    parser.add_argument('-cpm', '--cells_per_meter', type=float, required=True, help='Scale of cells to a meter on Occupancy Grid')
    
    args = parser.parse_args()
    
    cells_per_meter = args.cells_per_meter
    image_name = os.path.basename(args.image_path).rsplit('.', 1)[0]
    
    try:
        im = Image.open(args.image_path)
    except Exception as e:
        print("Error opening image due to exception: ", str(e))
        sys.exit(1)
    
    npdata_as_bytes = process_image(im)
    
    # Create Occupancy Grid Object
    occupancy_grid_obj = ALPSOccupancyGrid(
            cellsPerMeter = cells_per_meter,
            bytesPerCell = 4,
            width = im.size[0],
            height = im.size[1],
            grid = npdata_as_bytes
        )
    
    print("OccupancyGrid Object Created")
    print(f"Occupancy Grid Size: Width {occupancy_grid_obj.width}, Height {occupancy_grid_obj.height}")
    
    # Serialize Occupancy Grid Object with protobuf built-in serializer
    serialized = occupancy_grid_obj.SerializeToString()
    
    # compress serialized bytes and write to disk
    compressor = lzma.LZMAFile(f"compressed_bytes_{image_name}.xz", mode="wb")
    compressor.write(serialized)
    compressor.close()
