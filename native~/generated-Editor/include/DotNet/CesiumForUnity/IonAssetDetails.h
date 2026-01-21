#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>

namespace DotNet::Reinterop {
class ObjectHandle;
}
namespace DotNet::System {
class Object;
}
namespace DotNet::System {
class String;
}

namespace DotNet::CesiumForUnity {

class IonAssetDetails {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit IonAssetDetails(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: IonAssetDetails(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  public: operator ::DotNet::System::Object() const;
  private: static void* (*CallFormatType_3GczHehc_XCRt9ReXGSrdQ)(void* type, void** reinteropException);
  public: static ::DotNet::System::String FormatType(const ::DotNet::System::String& type);
  private: static void* (*CallFormatDate_Wg__UxSmEJUgHx3kyfccFEw)(void* assetDate, void** reinteropException);
  public: static ::DotNet::System::String FormatDate(const ::DotNet::System::String& assetDate);
};

} // namespace DotNet::CesiumForUnity


