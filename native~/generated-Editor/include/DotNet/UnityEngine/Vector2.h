#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>

namespace DotNet::UnityEngine {
struct Vector2;
}

namespace DotNet::UnityEngine {

struct Vector2 {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: static void (*Construct_1B2M2Y8AsgTpgAmY7PhCfg)(::DotNet::UnityEngine::Vector2* pReturnValue, void** reinteropException);
  public: static Vector2 Construct();
  public: float x;
  public: float y;
};

} // namespace DotNet::UnityEngine


