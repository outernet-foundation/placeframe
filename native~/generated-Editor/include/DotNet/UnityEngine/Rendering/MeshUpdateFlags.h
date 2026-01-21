#pragma once

#include <cstdint>
#include <flags/flags.hpp>



namespace DotNet::UnityEngine::Rendering {

enum class MeshUpdateFlags : uint32_t {
  Default = 0,
  DontValidateIndices = 1,
  DontResetBoneBounds = 2,
  DontNotifyMeshUsers = 4,
  DontRecalculateBounds = 8,
};

} // namespace DotNet::UnityEngine::Rendering


ALLOW_FLAGS_FOR_ENUM(::DotNet::UnityEngine::Rendering::MeshUpdateFlags)