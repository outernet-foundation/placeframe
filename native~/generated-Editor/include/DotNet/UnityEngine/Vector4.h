#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>

namespace DotNet::UnityEngine {
struct Vector4;
}

namespace DotNet::UnityEngine {

struct Vector4 {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: static void (*Construct_HRdOMAw1wcknBRlYiWJ61Q)(float x, float y, float z, float w, ::DotNet::UnityEngine::Vector4* pReturnValue, void** reinteropException);
  public: static Vector4 Construct(float x, float y, float z, float w);
  private: static void (*Construct_1B2M2Y8AsgTpgAmY7PhCfg)(::DotNet::UnityEngine::Vector4* pReturnValue, void** reinteropException);
  public: static Vector4 Construct();
  public: float x;
  public: float y;
  public: float z;
  public: float w;
};

} // namespace DotNet::UnityEngine


