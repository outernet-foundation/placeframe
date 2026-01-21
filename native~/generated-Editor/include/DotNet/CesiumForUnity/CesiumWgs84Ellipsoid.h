#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>



namespace DotNet::CesiumForUnity {

class CesiumWgs84Ellipsoid {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  public: CesiumWgs84Ellipsoid() = delete;
};

} // namespace DotNet::CesiumForUnity


