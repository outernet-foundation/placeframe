#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>
#include <DotNet/UnityEngine/Rendering/VertexAttribute.h>
#include <DotNet/UnityEngine/Rendering/VertexAttributeFormat.h>



namespace DotNet::UnityEngine::Rendering {

struct VertexAttributeDescriptor {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  public: ::DotNet::UnityEngine::Rendering::VertexAttribute attribute;
  public: ::DotNet::UnityEngine::Rendering::VertexAttributeFormat format;
  public: ::std::int32_t dimension;
  public: ::std::int32_t stream;
};

} // namespace DotNet::UnityEngine::Rendering


