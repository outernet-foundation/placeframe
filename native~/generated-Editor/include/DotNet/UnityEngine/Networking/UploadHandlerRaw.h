#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>

namespace DotNet::Reinterop {
class ObjectHandle;
}
namespace DotNet::System {
template <typename T0> class Array1;
}
namespace DotNet::Unity::Collections {
template <typename T0> struct NativeArray1;
}
namespace DotNet::UnityEngine::Networking {
class UploadHandler;
}
namespace DotNet::System {
class Object;
}

namespace DotNet::UnityEngine::Networking {

class UploadHandlerRaw {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit UploadHandlerRaw(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: UploadHandlerRaw(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  private: static void* (*Construct_Wn8TTeG3Q36ufSfvO3m1sg)(void* data, void** reinteropException);
  public: UploadHandlerRaw(const ::DotNet::System::Array1<::std::uint8_t>& data);
  private: static void* (*Construct_j9VUe_obWzqxHm0yKnVCmg)(void* data, ::std::uint8_t transferOwnership, void** reinteropException);
  public: UploadHandlerRaw(const ::DotNet::Unity::Collections::NativeArray1<::std::uint8_t>& data, bool transferOwnership);
  public: operator ::DotNet::UnityEngine::Networking::UploadHandler() const;
  public: operator ::DotNet::System::Object() const;
};

} // namespace DotNet::UnityEngine::Networking


