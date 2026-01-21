#pragma once

#include <DotNet/initializeReinterop.h>
#include <cstdint>
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>

namespace DotNet::Reinterop {
class ObjectHandle;
}
namespace DotNet::CesiumForUnity {
class CesiumCreditComponent;
}
namespace DotNet::System::Collections::Generic {
template <typename T0> class List1;
}
namespace DotNet::System {
class Object;
}

namespace DotNet::CesiumForUnity {

class CesiumCredit {
  private: friend std::uint8_t (::initializeReinterop)(std::uint64_t validationHash, void** functionPointers, std::int32_t count);
  private: ::DotNet::Reinterop::ObjectHandle _handle;
  public: explicit CesiumCredit(::DotNet::Reinterop::ObjectHandle&& handle) noexcept;
  public: CesiumCredit(std::nullptr_t) noexcept;
  public: bool operator==(std::nullptr_t) const noexcept;
  public: bool operator!=(std::nullptr_t) const noexcept;
  public: const ::DotNet::Reinterop::ObjectHandle& GetHandle() const;
  public: ::DotNet::Reinterop::ObjectHandle& GetHandle();
  private: static void* (*Construct_1B2M2Y8AsgTpgAmY7PhCfg)(void** reinteropException);
  public: CesiumCredit();
  private: static void* (*Construct_qXRB_eg5WNz__5KHXUesADw)(void* components, void** reinteropException);
  public: CesiumCredit(const ::DotNet::System::Collections::Generic::List1<::DotNet::CesiumForUnity::CesiumCreditComponent>& components);
  public: operator ::DotNet::System::Object() const;
  private: static void* (*Property_get_components)(void* thiz, void** reinteropException);
  public: ::DotNet::System::Collections::Generic::List1<::DotNet::CesiumForUnity::CesiumCreditComponent> components() const;
};

} // namespace DotNet::CesiumForUnity


