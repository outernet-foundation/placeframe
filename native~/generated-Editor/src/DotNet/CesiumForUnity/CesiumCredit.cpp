#include <DotNet/CesiumForUnity/CesiumCredit.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/Reinterop/ReinteropNativeException.h>
#include <DotNet/CesiumForUnity/CesiumCreditComponent.h>
#include <DotNet/System/Collections/Generic/List1.h>
#include <DotNet/System/Object.h>



namespace DotNet::CesiumForUnity {

CesiumCredit::CesiumCredit(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


CesiumCredit::CesiumCredit(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool CesiumCredit::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool CesiumCredit::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& CesiumCredit::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& CesiumCredit::GetHandle() {
    return this->_handle;
}


void* (*CesiumCredit::Construct_1B2M2Y8AsgTpgAmY7PhCfg)(void** reinteropException) = nullptr;


CesiumCredit::CesiumCredit()
    : _handle([&]() mutable {
        void* reinteropException = nullptr;
        void* handle = Construct_1B2M2Y8AsgTpgAmY7PhCfg(&reinteropException);
        if (reinteropException != nullptr)
            throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
        return handle;
    }())
{
}


void* (*CesiumCredit::Construct_qXRB_eg5WNz__5KHXUesADw)(void* components, void** reinteropException) = nullptr;


CesiumCredit::CesiumCredit(const ::DotNet::System::Collections::Generic::List1<::DotNet::CesiumForUnity::CesiumCreditComponent>& components)
    : _handle([&]() mutable {
        void* reinteropException = nullptr;
        void* handle = Construct_qXRB_eg5WNz__5KHXUesADw(components.GetHandle().GetRaw(), &reinteropException);
        if (reinteropException != nullptr)
            throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
        return handle;
    }())
{
}


CesiumCredit::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


void* (*DotNet::CesiumForUnity::CesiumCredit::Property_get_components)(void* thiz, void** reinteropException) = nullptr;


::DotNet::System::Collections::Generic::List1<::DotNet::CesiumForUnity::CesiumCreditComponent> CesiumCredit::components() const {
    void* reinteropException = nullptr;
    auto result = Property_get_components((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return ::DotNet::System::Collections::Generic::List1<::DotNet::CesiumForUnity::CesiumCreditComponent>(::DotNet::Reinterop::ObjectHandle(result));
}


} // namespace DotNet::CesiumForUnity


