#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>

namespace DotNet::UnityEngine::Networking {
class UnityWebRequest;
}
namespace DotNet::System {
class String;
}

namespace DotNet::UnityEngine::Networking {

class UnityWebRequestTexture {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  public: UnityWebRequestTexture() = delete;
  private: static void* (*CallGetTexture_Y2__l4HVQ8CbSg4jpXDip9A)(void* uri, void** reinteropException);
  public: static ::DotNet::UnityEngine::Networking::UnityWebRequest GetTexture(const ::DotNet::System::String& uri);
};

} // namespace DotNet::UnityEngine::Networking


