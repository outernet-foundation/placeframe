#include <DotNet/UnityEditor/IMGUI/Controls/MultiColumnHeader.h>
#include <utility> 
#include <DotNet/Reinterop/ObjectHandle.h>
#include <cstddef>
#include <DotNet/System/Object.h>
#include <cstdint>
#include <DotNet/Reinterop/ReinteropNativeException.h>



namespace DotNet::UnityEditor::IMGUI::Controls {

MultiColumnHeader::MultiColumnHeader(::DotNet::Reinterop::ObjectHandle&& handle) noexcept :
    _handle(std::move(handle)) {}


MultiColumnHeader::MultiColumnHeader(std::nullptr_t) noexcept : _handle(nullptr) {
}


bool MultiColumnHeader::operator==(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() == nullptr;
}


bool MultiColumnHeader::operator!=(std::nullptr_t) const noexcept {
    return this->_handle.GetRaw() != nullptr;
}


const ::DotNet::Reinterop::ObjectHandle& MultiColumnHeader::GetHandle() const {
    return this->_handle;
}


::DotNet::Reinterop::ObjectHandle& MultiColumnHeader::GetHandle() {
    return this->_handle;
}


MultiColumnHeader::operator ::DotNet::System::Object() const {
    return ::DotNet::System::Object(::DotNet::Reinterop::ObjectHandle(this->_handle));
}


::std::int32_t (*DotNet::UnityEditor::IMGUI::Controls::MultiColumnHeader::Property_get_sortedColumnIndex)(void* thiz, void** reinteropException) = nullptr;


::std::int32_t MultiColumnHeader::sortedColumnIndex() const {
    void* reinteropException = nullptr;
    auto result = Property_get_sortedColumnIndex((*this).GetHandle().GetRaw(), &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return result;
}


void (*DotNet::UnityEditor::IMGUI::Controls::MultiColumnHeader::Property_set_sortedColumnIndex)(void* thiz, ::std::int32_t value, void** reinteropException) = nullptr;


void MultiColumnHeader::sortedColumnIndex(::std::int32_t value) const {
    void* reinteropException = nullptr;
    Property_set_sortedColumnIndex((*this).GetHandle().GetRaw(), value, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
}


::std::uint8_t (*DotNet::UnityEditor::IMGUI::Controls::MultiColumnHeader::CallIsSortedAscending_ZiJhFqE0LPDoV__RgQlNVpQ)(void* thiz, ::std::int32_t columnIndex, void** reinteropException) = nullptr;


bool MultiColumnHeader::IsSortedAscending(::std::int32_t columnIndex) const {
    void* reinteropException = nullptr;
    auto result = CallIsSortedAscending_ZiJhFqE0LPDoV__RgQlNVpQ((*this).GetHandle().GetRaw(), columnIndex, &reinteropException);
    if (reinteropException != nullptr)
        throw Reinterop::ReinteropNativeException(::DotNet::System::Exception(::DotNet::Reinterop::ObjectHandle(reinteropException)));
    return !!result;
}


} // namespace DotNet::UnityEditor::IMGUI::Controls


