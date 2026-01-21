#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>
#include <DotNet/UnityEngine/Bounds.h>
#include <DotNet/UnityEngine/MeshTopology.h>

namespace DotNet::UnityEngine::Rendering {
struct SubMeshDescriptor;
}
namespace DotNet::UnityEngine {
enum class MeshTopology;
}

namespace DotNet::UnityEngine::Rendering {

struct SubMeshDescriptor {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: static void (*Construct_hVqvzF5fyHzN08NI0LUuIw)(::std::int32_t indexStart, ::std::int32_t indexCount, ::std::uint32_t topology, ::DotNet::UnityEngine::Rendering::SubMeshDescriptor* pReturnValue, void** reinteropException);
  public: static SubMeshDescriptor Construct(::std::int32_t indexStart, ::std::int32_t indexCount, ::DotNet::UnityEngine::MeshTopology topology);
  public: ::DotNet::UnityEngine::Bounds bounds;
  public: ::DotNet::UnityEngine::MeshTopology topology;
  public: ::std::int32_t indexStart;
  public: ::std::int32_t indexCount;
  public: ::std::int32_t baseVertex;
  public: ::std::int32_t firstVertex;
  public: ::std::int32_t vertexCount;
};

} // namespace DotNet::UnityEngine::Rendering


