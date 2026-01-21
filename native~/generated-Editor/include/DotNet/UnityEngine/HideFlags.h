#pragma once

#include <cstdint>
#include <flags/flags.hpp>



namespace DotNet::UnityEngine {

enum class HideFlags : uint32_t {
  None = 0,
  HideInHierarchy = 1,
  HideInInspector = 2,
  DontSaveInEditor = 4,
  NotEditable = 8,
  DontSaveInBuild = 16,
  DontUnloadUnusedAsset = 32,
  DontSave = 52,
  HideAndDontSave = 61,
};

} // namespace DotNet::UnityEngine


ALLOW_FLAGS_FOR_ENUM(::DotNet::UnityEngine::HideFlags)