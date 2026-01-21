#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>
#include <DotNet/UnityEngine/Vector3.h>

namespace DotNet::UnityEngine {
struct Vector3;
}
namespace DotNet::UnityEngine {
struct Bounds;
}

namespace DotNet::UnityEngine {

struct Bounds {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: static void (*Construct_Qy9aU2ShAPtxkIq6r1DXbA)(const ::DotNet::UnityEngine::Vector3* center, const ::DotNet::UnityEngine::Vector3* size, ::DotNet::UnityEngine::Bounds* pReturnValue, void** reinteropException);
  public: static Bounds Construct(const ::DotNet::UnityEngine::Vector3& center, const ::DotNet::UnityEngine::Vector3& size);
  private: ::DotNet::UnityEngine::Vector3 m_Center;
  private: ::DotNet::UnityEngine::Vector3 m_Extents;
};

} // namespace DotNet::UnityEngine


