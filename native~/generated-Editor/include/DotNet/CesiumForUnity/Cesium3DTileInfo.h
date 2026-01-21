#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>
#include <DotNet/UnityEngine/Vector3.h>



namespace DotNet::CesiumForUnity {

struct Cesium3DTileInfo {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  public: bool usesAdditiveRefinement;
  public: float geometricError;
  public: ::DotNet::UnityEngine::Vector3 dimensions;
  public: bool isTranslucent;
};

} // namespace DotNet::CesiumForUnity


